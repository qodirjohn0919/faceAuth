# faceAuth

A Django-based employee attendance system that uses face recognition (OpenCV LBPH) to automatically check employees in and out.

## Features

- Register employees with a live webcam photo
- Face recognition check-in / check-out via webcam
- Late arrival detection (work starts at 09:00)
- Dashboard with today's attendance summary
- Filterable attendance history
- Employee detail page with attendance stats
- Django admin panel

## Requirements

- Python 3.10
- Windows (setup script is PowerShell)

## Setup

```powershell
# Clone and set up in one step
.\setup.ps1 -GitUrl https://github.com/qodirjohn0919/faceAuth.git

# Or if already cloned
.\setup.ps1
```

The script will:
1. Create a virtual environment
2. Install all dependencies (`Django`, `opencv-contrib-python`, `numpy`, `Pillow`)
3. Run database migrations
4. Create `media/faces/` directory
5. Optionally create a Django superuser

## Running

```powershell
venv\Scripts\activate
python manage.py runserver
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Project Structure

```
faceAuth/
├── attendance/         # Main app (models, views, face utils)
├── faceid/             # Django project settings & URLs
├── templates/          # HTML templates
├── static/             # CSS
├── media/              # Face images (gitignored)
├── manage.py
└── setup.ps1           # One-command setup script
```

## Configuration

Key settings in `faceid/settings.py`:

| Setting | Default | Description |
|---|---|---|
| `WORK_START_TIME` | `9:00` | Late threshold for check-in |
| `WORK_END_TIME` | `18:00` | End of work day |
| `FACE_MATCH_THRESHOLD` | `80.0` | LBPH confidence threshold (lower = stricter) |

## Tech Stack

- **Backend:** Django 5.2
- **Face Recognition:** OpenCV LBPH (`opencv-contrib-python`)
- **Database:** SQLite
- **Frontend:** HTML/CSS with webcam capture via JavaScript
