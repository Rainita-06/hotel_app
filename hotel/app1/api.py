import io, base64, qrcode
from django.urls import reverse
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView
from rest_framework.decorators import api_view, permission_classes, action
from django.utils.dateparse import parse_date
from django.db.models import Count
from datetime import timedelta

from app1.models import Complaint, Review, UserGroup, Users, Location, Voucher, Department
from app1.serializers import (
    ComplaintSerializer, ReviewSerializer, UserGroupSerializer, UsersSerializer, LocationSerializer,
    VoucherSerializer, DepartmentSerializer
)
from app1.permissions import IsAdminForMaster


# ---------- MASTER endpoints (Admin only) ----------
class MasterUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Users.objects.all().order_by("-created_at")
    serializer_class = UsersSerializer
    permission_classes = [IsAuthenticated, IsAdminForMaster]


class MasterLocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all().order_by("name")
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated, IsAdminForMaster]


# ---------- Voucher CRUD (replaces BreakfastVoucher) ----------
class VoucherViewSet(viewsets.ModelViewSet):
    """
    CRUD:
    GET /api/vouchers/
    POST /api/vouchers/ (QR auto-generated)
    GET /api/vouchers/{id}/
    PUT /api/vouchers/{id}/
    PATCH /api/vouchers/{id}/
    DELETE /api/vouchers/{id}/
    """
    queryset = Voucher.objects.all().order_by("-created_at")
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        voucher = serializer.save(created_at=timezone.now())
        try:
            page_url = self.request.build_absolute_uri(
                reverse("room_detail", args=[voucher.voucher_id])
            )
        except Exception:
            page_url = self.request.build_absolute_uri(f"/api/room/{voucher.voucher_id}/")

        img = qrcode.make(page_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_png_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        voucher.qr_code = page_url
        voucher.save(update_fields=["qr_code"])

        self.qr_png_b64 = qr_png_b64

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if hasattr(self, "qr_png_b64"):
            response.data["qr_png_base64"] = self.qr_png_b64
        return response


# ---------- Dashboard QR Generator ----------
class QRGenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        room_no = request.data.get("room_no")
        customer_name = request.data.get("customer_name")
        date_str = request.data.get("date")

        if not room_no or not customer_name or not date_str:
            return Response(
                {"detail": "room_no, customer_name and date are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        voucher = Voucher.objects.create(
            customer_name=customer_name,
            room_no=room_no,
            qty=1,
            status="Active",
            created_at=timezone.now(),
        )

        try:
            page_url = request.build_absolute_uri(
                reverse("room_detail", args=[voucher.voucher_id])
            )
        except Exception:
            page_url = request.build_absolute_uri(f"/api/room/{voucher.voucher_id}/")

        img = qrcode.make(page_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_png_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        voucher.qr_code = page_url
        voucher.save(update_fields=["qr_code"])

        data = {
            "voucher_id": voucher.voucher_id,
            "room_no": voucher.room_no,
            "customer_name": voucher.customer_name,
            "status": voucher.status,
            "qr_url": page_url,
            "qr_png_base64": qr_png_b64,
        }
        return Response(data, status=status.HTTP_201_CREATED)


# ---------- Room detail ----------
class RoomDetailAPIView(RetrieveAPIView):
    queryset = Voucher.objects.all()
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get(self, request, *args, **kwargs):
        voucher = self.get_object()
        if voucher.status != "Checked":
            voucher.status = "Checked"
            voucher.save(update_fields=["status"])
        return super().get(request, *args, **kwargs)


# ---------- Reporting APIs ----------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def checked_in_customers(request):
    vouchers = Voucher.objects.filter(status="Checked")
    serializer = VoucherSerializer(vouchers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def visits_by_date(request):
    date_str = request.query_params.get("date")
    if not date_str:
        return Response({"detail": "Please provide ?date=YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

    parsed_date = parse_date(date_str)
    if not parsed_date:
        return Response({"detail": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

    vouchers = Voucher.objects.filter(created_at__date=parsed_date)
    count = vouchers.count()
    customers = vouchers.values("customer_name", "room_no")

    return Response(
        {"date": date_str, "total_visits": count, "customers": list(customers)},
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def visits_weekly(request):
    start_str = request.query_params.get("start")
    if not start_str:
        return Response({"detail": "Please provide ?start=YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

    start_date = parse_date(start_str)
    if not start_date:
        return Response({"detail": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)

    end_date = start_date + timedelta(days=6)
    vouchers = (
        Voucher.objects
        .filter(created_at__date__range=(start_date, end_date))
        .values("created_at__date")
        .annotate(total=Count("voucher_id"))
        .order_by("created_at__date")
    )

    return Response(
        {"week_start": start_date, "week_end": end_date, "daily_visits": list(vouchers)},
        status=status.HTTP_200_OK
    )

# app1/views.py

from .models import Building, Checklist, ChecklistItem, Department, Floor, LocationFamily, LocationType, RequestFamily, RequestType, Users, Complaint, WorkFamily, Workflow
from .serializers import BuildingSerializer, ChecklistItemSerializer, ChecklistSerializer, DepartmentSerializer, FloorSerializer, LocationFamilySerializer, LocationTypeSerializer, RequestFamilySerializer, RequestTypeSerializer, UsersSerializer, ComplaintSerializer, WorkFamilySerializer, WorkflowSerializer

# ✅ CRUD ViewSet for Department
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

# ✅ Extra API for linked users and complaints
class DepartmentDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            dept = Department.objects.get(pk=pk)
        except Department.DoesNotExist:
            return Response({"error": "Department not found"}, status=404)

        users = Users.objects.filter(department=dept)
        complaints = Complaint.objects.filter(user__department=dept)

        return Response({
            "department": DepartmentSerializer(dept).data,
            "users": UsersSerializer(users, many=True).data,
            "complaints": ComplaintSerializer(complaints, many=True).data,
        })

# # ---------- Department CRUD ----------
# class DepartmentViewSet(viewsets.ModelViewSet):
#     queryset = Department.objects.all().order_by("name")
#     serializer_class = DepartmentSerializer
#     filter_backends = [filters.SearchFilter, filters.OrderingFilter]
#     search_fields = ["name"]
#     ordering_fields = ["name"]

#     def get_permissions(self):
#         if self.action in ["list", "retrieve"]:
#             return [IsAuthenticated()]
#         return [IsAuthenticated(), IsAdminForMaster()]

#     @action(detail=True, methods=["get"], url_path="users", permission_classes=[IsAuthenticated])
#     def users(self, request, pk=None):
#         users = Users.objects.filter(department_id=pk).order_by("full_name")
#         page = self.paginate_queryset(users)
#         ser = UsersSerializer(page or users, many=True)
#         return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)


# ---------- Location CRUD ----------
class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all().order_by("name")
    serializer_class = LocationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "room_no", "building__name", "floor__floor_number"]
    ordering_fields = ["name", "room_no", "capacity"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminForMaster()]


# ---------- Users CRUD ----------
class UsersViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.select_related("department").all().order_by("-created_at")
    serializer_class = UsersSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["full_name", "email", "phone", "title", "department__name"]
    ordering_fields = ["created_at", "full_name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminForMaster()]

    @action(detail=False, methods=["get"], url_path="by-department/(?P<dept_id>[^/.]+)", permission_classes=[IsAuthenticated])
    def by_department(self, request, dept_id=None):
        qs = self.get_queryset().filter(department_id=dept_id)
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer


class UserGroupViewSet(viewsets.ModelViewSet):
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer

class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer

class LocationFamilyViewSet(viewsets.ModelViewSet):
    queryset = LocationFamily.objects.all()
    serializer_class = LocationFamilySerializer

class LocationTypeViewSet(viewsets.ModelViewSet):
    queryset = LocationType.objects.all()
    serializer_class = LocationTypeSerializer

class RequestFamilyViewSet(viewsets.ModelViewSet):
    queryset = RequestFamily.objects.all()
    serializer_class = RequestFamilySerializer

class WorkFamilyViewSet(viewsets.ModelViewSet):
    queryset = WorkFamily.objects.all()
    serializer_class = WorkFamilySerializer

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer

class RequestTypeViewSet(viewsets.ModelViewSet):
    queryset = RequestType.objects.all()
    serializer_class = RequestTypeSerializer

class ChecklistViewSet(viewsets.ModelViewSet):
    queryset = Checklist.objects.all()
    serializer_class = ChecklistSerializer
    permission_classes = [IsAuthenticated]

class ChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItem.objects.all()
    serializer_class = ChecklistItemSerializer
    permission_classes = [IsAuthenticated]



