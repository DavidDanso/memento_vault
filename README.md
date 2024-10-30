# Memento Vault

## Overview
Memento Vault is a platform designed to securely store and share photos and videos from special events, enhanced with AI-driven features for seamless organization and content management.

## Features

### Core Functionality
1. **User Authentication**
   - Secure sign-up/login with email verification.
   - Password reset functionality.

2. **Vault Creation with QR Code**
   - Create vaults for events.
   - Automatic QR code generation.
   - Customizable QR code appearance.

3. **Photo/Video Upload via QR Code**
   - Scan QR codes to access upload pages.
   - Multiple file upload with progress indicators.

4. **Timeline View**
   - Chronological display of media with infinite scroll.
   - Thumbnail grid with date separators.

5. **Basic Media Editing**
   - Add/edit captions and tags.
   - Batch editing for multiple media.

6. **Simple Sharing**
   - Share vaults via view-only links.
   - Set expiration dates for shared links.

7. **Privacy Controls**
   - Toggle vault privacy.
   - Manage sharing settings for individual files.

8. **User Dashboard**
   - View all vaults and recent uploads.
   - Display of total media and storage usage.

9. **Mobile Responsiveness**
   - Fully responsive design.
   - Mobile-optimized layout and touch-friendly interface.

10. **Account Settings**
    - Manage profile, notifications, and connected devices.

### AI-Enhanced Features (In Development)
11. **Smart Captioning** *(In Progress)*
    - AI-generated captions for media.
    - Editable and learnable captions.

12. **Emotion Detection** *(In Progress)*
    - Detects emotions in photos.
    - Tags media with emotion-based filters.

13. **Similar Photo Grouping** *(In Progress)*
    - Groups similar photos.
    - Suggests best photo, with option to keep/discard duplicates.

14. **Personalized Content Surfacing** *(In Progress)*
    - Highlights favorite memories.
    - Suggests collections based on preferences.

*Note: Some of the AI-driven features are still being developed and will be available in future updates.*

## MVP Pages

1. **Landing Page**
   - Feature highlights, sign-up/login, and how-to section.

2. **Sign Up / Login Page**
   - Clean forms with social media login options.

3. **User Dashboard**
   - Overview of vaults, recent uploads, and AI suggestions.

4. **Vault Creation Page**
   - Form to name and describe vaults.
   - QR code generation and sharing options.

5. **Vault Detail Page**
   - Media timeline, upload button, and sharing controls.

6. **Media Upload Page**
   - Drag-and-drop interface with file progress bars.

7. **Individual Media View**
   - Full-size media with AI-generated captions and emotion tags.

8. **Media Editing Page**
   - Tools for editing captions, tags, and privacy.

9. **Sharing Management**
   - Overview of shared links and permission settings.

10. **Account Settings**
    - Manage personal information, storage, and notifications.

11. **Help/FAQ Page**
    - User guide, tutorials, and support options.

## Installation

### Prerequisites
- Python 3.x
- Django
- AWS SDK (boto3)
- PostgreSQL

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/memento-vault.git
   cd memento-vault


2. Install dependencies:
   ```bash
   pip install -r requirements.txt


3. Set up environment variables (see .env.example for reference).
   

4. Run database migrations:
   ```bash
   python manage.py migrate


5. Start the development server:
   ```bash
   python manage.py runserver


## Usage

- Access the app via http://localhost:8000
- Sign up to create your first vault, generate QR codes, and start uploading media.


Note: I am actively developing new features, so expect frequent updates as the platform continues to improve.
