from django.core.management.base import BaseCommand
from members.models import Member


class Command(BaseCommand):
    help = "Sincroniza y crea cuentas de usuario y rutinas para todos los socios registrados."

    def handle(self, *args, **options):
        self.stdout.write("Sincronizando cuentas de usuario para los socios...")
        members = Member.objects.all()
        created_count = 0
        routine_count = 0

        for member in members:
            user = member.create_or_sync_user_account()
            if user:
                created_count += 1
            member.assign_default_routine_if_none()
            if member.routines.exists():
                routine_count += 1

        self.stdout.write(self.style.SUCCESS(f"[OK] Sincronizados {created_count} usuarios de acceso para {members.count()} socios."))
        self.stdout.write(self.style.SUCCESS(f"[OK] {routine_count} socios cuentan con rutinas activas."))
