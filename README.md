# Memento Vault

## Overview
Memento Vault is a platform designed to securely store photos and videos from special events, enhanced with AI-driven features for seamless organization and content management.

## Usage

- Access the app via [Memento Vault](https://vault-memento.onrender.com)

- Sign up to create your first vault, generate QR codes, and start uploading media.

  
## Features

### Core Functionality
1. **User Authentication**
   - Secure sign-up/login with email verification.
   - Password reset functionality.

2. **Vault Creation with QR Code**
   - Create vaults for events.
   - Automatic QR code generation.

3. **Photo/Video Upload via QR Code**
   - Scan QR codes to access upload pages.
   - Multiple file upload with progress indicator.

4. **Timeline View**
   - Chronological display of media with infinite scroll.
   - Thumbnail grid view.

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
   


## App Preview:

<table width="100%"> 
<tr>
<td width="50%">      
&nbsp; 
<br>
<p align="center">
  Landing Page
</p>
<img src="https://github.com/DavidDanso/memento_vault/blob/main/static/images/ui/landing_page.png" />
</td> 
<td width="50%">
<br>
<p align="center">
  Dashboard(login)
</p>
<img src="https://github.com/DavidDanso/memento_vault/blob/main/static/images/ui/dashboard.png" />
</td>
</table>

<table width="100%"> 
<tr>
<td width="50%">      
&nbsp; 
<br>
<p align="center">
  Empty Vault Page
</p>
<img src="https://github.com/DavidDanso/memento_vault/blob/main/static/images/ui/empty_vault.png" />
</td> 
<td width="50%">
<br>
<p align="center">
  Vault Details Page
</p>
<img src="https://github.com/DavidDanso/memento_vault/blob/main/static/images/ui/vault_details.png" />
</td>
</table>



### AI-Enhanced Features
11. **Smart Captioning**
    - AI-generated captions for media.
    - Editable and learnable captions.(In Development)

12. **Emotion Detection**
    - Detects emotions in photos.
    - Tags media with emotion-based filters.

13. **Similar Photo Grouping** *(In Development)*
    - Groups similar photos.
    - Suggests best photo, with option to keep/discard duplicates.

14. **Personalized Content Surfacing** *(In Development)*
    - Highlights favorite memories.
    - Suggests collections based on preferences.

*Note: Some of the AI-driven features are still being developed and will be available in future updates.*

## MVP Pages

1. **Landing Page**
   - Feature highlights, sign-up/login, and how-to section.

2. **Sign Up / Login Page**
   - Clean forms with social media login options.

3. **User Dashboard**
   - Overview of vaults, and recent uploads.

4. **Vault Creation Page**
   - Form to name and describe vaults.
   - Automatic QR code generation.

5. **Vault Detail Page**
   - Media timeline, and upload button.

6. **Media Upload Page**
   - Drag-and-drop interface with file progress bars.

7. **Individual Media View**
   - Full-size media with AI-generated captions and emotion tags.

8. **Account Settings**
    - Manage personal information, storage, and notifications.

## Installation

### Prerequisites
- Python 3.x
- Django
- Cloudinary Python SDK
- PostgreSQL

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/DavidDanso/memento-vault.git
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


Note: I am actively developing new features, so expect frequent updates as the platform continues to improve.
