"""
Management command: reencode_faces
----------------------------------
Re-generates LBPH-compatible encodings for every active employee whose face
photo is stored on disk, without requiring employees to re-sit for the camera.

Usage:
    python manage.py reencode_faces

Options:
    --dry-run   Print what would happen without saving anything.
    --employee  Process a single employee by their employee_id.
"""

import os
import cv2
from django.core.management.base import BaseCommand
from django.conf import settings

from attendance.models import Employee
from attendance import face_utils


class Command(BaseCommand):
    help = 'Re-encode stored face photos using the new OpenCV/LBPH backend.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without writing to the database.',
        )
        parser.add_argument(
            '--employee',
            type=str,
            default=None,
            help='Process only this employee_id (default: all active employees).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        single_id = options['employee']

        qs = Employee.objects.filter(is_active=True)
        if single_id:
            qs = qs.filter(employee_id=single_id)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No matching employees found.'))
            return

        self.stdout.write(
            self.style.HTTP_INFO(
                f'Processing {total} employee(s){"  [DRY RUN]" if dry_run else ""}...\n'
            )
        )

        ok = 0
        skipped = 0
        failed = 0

        for emp in qs:
            # Resolve the photo path
            photo_path = None
            if emp.photo:
                # emp.photo stores a relative path like 'faces/EMP001_face.jpg'
                candidate = os.path.join(settings.MEDIA_ROOT, str(emp.photo))
                if os.path.isfile(candidate):
                    photo_path = candidate

            if photo_path is None:
                self.stdout.write(
                    self.style.WARNING(
                        f'  SKIP  {emp.employee_id} ({emp.full_name()}) — photo not found on disk'
                    )
                )
                skipped += 1
                continue

            # Load and encode
            img = cv2.imread(photo_path)
            if img is None:
                self.stdout.write(
                    self.style.ERROR(
                        f'  FAIL  {emp.employee_id} ({emp.full_name()}) — cv2.imread returned None'
                    )
                )
                failed += 1
                continue

            encoding = face_utils.get_face_encoding(img)
            if encoding is None:
                self.stdout.write(
                    self.style.ERROR(
                        f'  FAIL  {emp.employee_id} ({emp.full_name()}) — no face detected in photo'
                    )
                )
                failed += 1
                continue

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  OK    {emp.employee_id} ({emp.full_name()}) — encoding length {len(encoding)} [not saved]'
                    )
                )
            else:
                emp.set_face_encoding(encoding)
                emp.save(update_fields=['face_encoding', 'updated_at'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  OK    {emp.employee_id} ({emp.full_name()}) — saved ({len(encoding)} values)'
                    )
                )
            ok += 1

        self.stdout.write('')
        self.stdout.write(
            f'Done. OK: {ok}  |  Skipped (no photo): {skipped}  |  Failed: {failed}'
        )
        if failed > 0:
            self.stdout.write(
                self.style.WARNING(
                    'Employees marked FAIL must re-register manually via /register/.'
                )
            )
