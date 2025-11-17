// Translation Dictionary
const translations = {
    en: {
        // Navbar
        "nav.home": "Home",
        "nav.browse": "Browse",
        "nav.library": "Library",
        "nav.upload": "Upload",
        "nav.admin": "Admin",
        "nav.logout": "Logout",
        "nav.login": "Login",
        "nav.signup": "Sign Up",
        "search.placeholder": "Search podcasts...",

        // Footer
        "footer.about_title": "Arab Podcast",
        "footer.about_text": "Your premier destination for high-quality podcasts across all genres and topics.",
        "footer.quicklinks_title": "Quick Links",
        "footer.categories_title": "Categories",
        "footer.follow_title": "Follow Us",
        "footer.copyright": "© 2024 Arab Podcast. All rights reserved.",

        // Categories
        "category.technology": "Technology",
        "category.business": "Business",
        "category.education": "Education",
        "category.entertainment": "Entertainment",

        // Common
        "common.loading": "Loading...",
        "common.error": "Error",
        "common.success": "Success",
        "common.cancel": "Cancel",
        "common.save": "Save",
        "common.delete": "Delete",
        "common.edit": "Edit",
        "common.create": "Create",
        "common.view": "View",

        // Upload Page
        "upload.title": "Upload Your Podcast",
        "upload.subtitle": "Share your voice with the world",
        "upload.basic_info": "Basic Information",
        "upload.podcast_title": "Podcast Title",
        "upload.description": "Description",
        "upload.description_placeholder": "Describe your podcast...",
        "upload.description_hint": "Give listeners a compelling overview of your content",
        "upload.category": "Category",
        "upload.select_category": "Select a category",
        "upload.media_type": "Content Type",
        "upload.voice_only": "Voice Only (صوت فقط)",
        "upload.video": "Video",
        "upload.media_file": "Media File",
        "upload.audio_file": "Audio File",
        "upload.video_file": "Video File",
        "upload.click_upload": "Click to upload or drag and drop",
        "upload.audio_formats": "MP3, WAV, M4A, OGG (Max 500MB)",
        "upload.video_formats": "MP4, AVI, MOV, WMV, FLV, MKV, WEBM (Max 500MB)",
        "upload.cover_image": "Cover Image",
        "upload.image_formats": "PNG, JPG, JPEG, WEBP (Recommended: 1:1 ratio)",
        "upload.submit": "Upload Podcast",
        "upload.uploading": "Uploading...",

        // Validation Messages
        "validation.title_required": "Please enter a podcast title",
        "validation.title_short": "Title must be at least 3 characters long",
        "validation.category_required": "Please select a category",
        "validation.audio_required": "Please upload an audio file (MP3, WAV, M4A, or OGG)",
        "validation.video_required": "Please upload a video file (MP4, AVI, MOV, WMV, FLV, MKV, or WEBM)",
        "validation.file_too_large": "File is too large. Maximum size is 500MB",
        "validation.file_empty": "File is empty. Please select a valid file",
        "validation.invalid_format": "Invalid audio file format. Please upload MP3, WAV, M4A, or OGG",
        "validation.invalid_video_format": "Invalid video file format. Please upload MP4, AVI, MOV, WMV, FLV, MKV, or WEBM",

        // Login Page
        "login.title": "Welcome Back",
        "login.subtitle": "Sign in to continue to Arab Podcast",
        "login.demo_title": "Demo Admin Account",
        "login.username": "Username:",
        "login.password": "Password:",
        "login.username_email": "Username or Email",
        "login.username_placeholder": "Enter your username or email",
        "login.password_label": "Password",
        "login.password_placeholder": "Enter your password",
        "login.remember": "Remember me",
        "login.forgot": "Forgot password?",
        "login.signin": "Sign In",
        "login.no_account": "Don't have an account?",

        // Register Page
        "register.title": "Create Account",
        "register.subtitle": "Join the podcast community today",
        "register.username": "Username",
        "register.username_placeholder": "Choose a unique username",
        "register.username_error": "Username must be at least 3 characters and contain only letters, numbers, and underscores",
        "register.email": "Email Address",
        "register.email_placeholder": "your.email@example.com",
        "register.email_error": "Please enter a valid email",
        "register.fullname": "Full Name",
        "register.fullname_placeholder": "Your full name (optional)",
        "register.password_label": "Password",
        "register.password_placeholder": "Choose a strong password",
        "register.password_error": "Password must be at least 6 characters",
        "register.confirm_password": "Confirm Password",
        "register.confirm_placeholder": "Re-enter your password",
        "register.confirm_error": "Passwords do not match",
        "register.signup": "Sign Up",
        "register.have_account": "Already have an account?",

        // Podcast Detail
        "podcast.like": "Like",
        "podcast.liked": "Liked",
        "podcast.save_playlist": "Save to Playlist",
        "podcast.plays": "Plays",
        "podcast.favorites": "Favorites",
        "podcast.about": "About this podcast",
        "podcast.comments": "Comments",
        "podcast.post_comment": "Post Comment",
        "podcast.share_thoughts": "Share your thoughts...",
        "podcast.login_comment": "to leave a comment",
        "podcast.related": "Related Podcasts",

        // Playlist Modal
        "playlist.save_to": "Save to Playlist",
        "playlist.create_new": "Create New Playlist",
        "playlist.name": "Playlist Name",
        "playlist.name_placeholder": "My Playlist",
        "playlist.description": "Description (Optional)",
        "playlist.description_placeholder": "Add a description",
        "playlist.create": "Create Playlist",
        "playlist.no_playlists": "No playlists yet. Create one below!",
        "playlist.podcasts": "podcasts",
        "playlist.added": "Added to",
        "playlist.already_exists": "Podcast already in playlist",
        "playlist.created": "Playlist created successfully!",

        // Admin
        "admin.dashboard": "Dashboard",
        "admin.users": "Users",
        "admin.podcasts": "Podcasts",
        "admin.categories": "Categories",
        "admin.back": "Back to Site",
        "admin.overview": "Dashboard Overview",
        "admin.welcome": "Welcome back",
        "admin.happening": "Here's what's happening with your platform",
        "admin.total_users": "Total Users",
        "admin.total_podcasts": "Total Podcasts",
        "admin.total_plays": "Total Plays",
        "admin.total_comments": "Total Comments",
        "admin.recent_podcasts": "Recent Podcasts",
        "admin.recent_users": "Recent Users",
        "admin.manage_users": "Manage Users",
        "admin.manage_podcasts": "Manage Podcasts",
        "admin.manage_categories": "Manage Categories",
        "admin.view_manage": "View and manage all",
    },

    ar: {
        // Navbar
        "nav.home": "الرئيسية",
        "nav.browse": "تصفح",
        "nav.library": "مكتبتي",
        "nav.upload": "رفع",
        "nav.admin": "الإدارة",
        "nav.logout": "تسجيل خروج",
        "nav.login": "تسجيل دخول",
        "nav.signup": "إنشاء حساب",
        "search.placeholder": "ابحث عن البودكاست...",

        // Footer
        "footer.about_title": "بودكاست عربي",
        "footer.about_text": "وجهتك المفضلة للبودكاست عالي الجودة عبر جميع الأنواع والمواضيع.",
        "footer.quicklinks_title": "روابط سريعة",
        "footer.categories_title": "التصنيفات",
        "footer.follow_title": "تابعنا",
        "footer.copyright": "© 2024 بودكاست عربي. جميع الحقوق محفوظة.",

        // Categories
        "category.technology": "التكنولوجيا",
        "category.business": "الأعمال",
        "category.education": "التعليم",
        "category.entertainment": "الترفيه",

        // Common
        "common.loading": "جاري التحميل...",
        "common.error": "خطأ",
        "common.success": "نجح",
        "common.cancel": "إلغاء",
        "common.save": "حفظ",
        "common.delete": "حذف",
        "common.edit": "تعديل",
        "common.create": "إنشاء",
        "common.view": "عرض",

        // Upload Page
        "upload.title": "ارفع البودكاست الخاص بك",
        "upload.subtitle": "شارك صوتك مع العالم",
        "upload.basic_info": "المعلومات الأساسية",
        "upload.podcast_title": "عنوان البودكاست",
        "upload.description": "الوصف",
        "upload.description_placeholder": "صف البودكاست الخاص بك...",
        "upload.description_hint": "قدم للمستمعين نظرة عامة مقنعة عن محتواك",
        "upload.category": "التصنيف",
        "upload.select_category": "اختر تصنيفاً",
        "upload.media_type": "نوع المحتوى",
        "upload.voice_only": "صوت فقط",
        "upload.video": "فيديو",
        "upload.media_file": "ملف الوسائط",
        "upload.audio_file": "ملف الصوت",
        "upload.video_file": "ملف الفيديو",
        "upload.click_upload": "انقر للرفع أو اسحب وأفلت",
        "upload.audio_formats": "MP3, WAV, M4A, OGG (الحد الأقصى 500 ميجابايت)",
        "upload.video_formats": "MP4, AVI, MOV, WMV, FLV, MKV, WEBM (الحد الأقصى 500 ميجابايت)",
        "upload.cover_image": "صورة الغلاف",
        "upload.image_formats": "PNG, JPG, JPEG, WEBP (يوصى بنسبة 1:1)",
        "upload.submit": "رفع البودكاست",
        "upload.uploading": "جاري الرفع...",

        // Validation Messages
        "validation.title_required": "الرجاء إدخال عنوان البودكاست",
        "validation.title_short": "يجب أن يكون العنوان 3 أحرف على الأقل",
        "validation.category_required": "الرجاء اختيار تصنيف",
        "validation.audio_required": "الرجاء رفع ملف صوتي (MP3, WAV, M4A, أو OGG)",
        "validation.video_required": "الرجاء رفع ملف فيديو (MP4, AVI, MOV, WMV, FLV, MKV, أو WEBM)",
        "validation.file_too_large": "الملف كبير جداً. الحد الأقصى هو 500 ميجابايت",
        "validation.file_empty": "الملف فارغ. الرجاء اختيار ملف صالح",
        "validation.invalid_format": "صيغة ملف الصوت غير صالحة. الرجاء رفع MP3, WAV, M4A, أو OGG",
        "validation.invalid_video_format": "صيغة ملف الفيديو غير صالحة. الرجاء رفع MP4, AVI, MOV, WMV, FLV, MKV, أو WEBM",

        // Login Page
        "login.title": "مرحباً بعودتك",
        "login.subtitle": "سجل دخولك للمتابعة إلى بودكاست عربي",
        "login.demo_title": "حساب المسؤول التجريبي",
        "login.username": "اسم المستخدم:",
        "login.password": "كلمة المرور:",
        "login.username_email": "اسم المستخدم أو البريد الإلكتروني",
        "login.username_placeholder": "أدخل اسم المستخدم أو البريد الإلكتروني",
        "login.password_label": "كلمة المرور",
        "login.password_placeholder": "أدخل كلمة المرور",
        "login.remember": "تذكرني",
        "login.forgot": "نسيت كلمة المرور؟",
        "login.signin": "تسجيل الدخول",
        "login.no_account": "ليس لديك حساب؟",

        // Register Page
        "register.title": "إنشاء حساب",
        "register.subtitle": "انضم إلى مجتمع البودكاست اليوم",
        "register.username": "اسم المستخدم",
        "register.username_placeholder": "اختر اسم مستخدم فريد",
        "register.username_error": "يجب أن يكون اسم المستخدم 3 أحرف على الأقل ويحتوي فقط على أحرف وأرقام وشرطات سفلية",
        "register.email": "عنوان البريد الإلكتروني",
        "register.email_placeholder": "your.email@example.com",
        "register.email_error": "الرجاء إدخال بريد إلكتروني صالح",
        "register.fullname": "الاسم الكامل",
        "register.fullname_placeholder": "اسمك الكامل (اختياري)",
        "register.password_label": "كلمة المرور",
        "register.password_placeholder": "اختر كلمة مرور قوية",
        "register.password_error": "يجب أن تكون كلمة المرور 6 أحرف على الأقل",
        "register.confirm_password": "تأكيد كلمة المرور",
        "register.confirm_placeholder": "أعد إدخال كلمة المرور",
        "register.confirm_error": "كلمات المرور غير متطابقة",
        "register.signup": "إنشاء حساب",
        "register.have_account": "لديك حساب بالفعل؟",

        // Podcast Detail
        "podcast.like": "إعجاب",
        "podcast.liked": "معجب به",
        "podcast.save_playlist": "حفظ في قائمة",
        "podcast.plays": "مرات التشغيل",
        "podcast.favorites": "المفضلة",
        "podcast.about": "حول هذا البودكاست",
        "podcast.comments": "التعليقات",
        "podcast.post_comment": "نشر تعليق",
        "podcast.share_thoughts": "شارك أفكارك...",
        "podcast.login_comment": "لترك تعليق",
        "podcast.related": "بودكاست ذات صلة",

        // Playlist Modal
        "playlist.save_to": "حفظ في قائمة التشغيل",
        "playlist.create_new": "إنشاء قائمة تشغيل جديدة",
        "playlist.name": "اسم قائمة التشغيل",
        "playlist.name_placeholder": "قائمتي",
        "playlist.description": "الوصف (اختياري)",
        "playlist.description_placeholder": "أضف وصفاً",
        "playlist.create": "إنشاء قائمة التشغيل",
        "playlist.no_playlists": "لا توجد قوائم تشغيل بعد. أنشئ واحدة أدناه!",
        "playlist.podcasts": "بودكاست",
        "playlist.added": "تمت الإضافة إلى",
        "playlist.already_exists": "البودكاست موجود بالفعل في القائمة",
        "playlist.created": "تم إنشاء قائمة التشغيل بنجاح!",

        // Admin
        "admin.dashboard": "لوحة التحكم",
        "admin.users": "المستخدمون",
        "admin.podcasts": "البودكاست",
        "admin.categories": "التصنيفات",
        "admin.back": "العودة للموقع",
        "admin.overview": "نظرة عامة على لوحة التحكم",
        "admin.welcome": "مرحباً بعودتك",
        "admin.happening": "إليك ما يحدث في منصتك",
        "admin.total_users": "إجمالي المستخدمين",
        "admin.total_podcasts": "إجمالي البودكاست",
        "admin.total_plays": "إجمالي مرات التشغيل",
        "admin.total_comments": "إجمالي التعليقات",
        "admin.recent_podcasts": "أحدث البودكاست",
        "admin.recent_users": "أحدث المستخدمين",
        "admin.manage_users": "إدارة المستخدمين",
        "admin.manage_podcasts": "إدارة البودكاست",
        "admin.manage_categories": "إدارة التصنيفات",
        "admin.view_manage": "عرض وإدارة الكل",
    }
};

// Translation function
function translate(key, lang) {
    return translations[lang][key] || translations['en'][key] || key;
}

// Apply translations to page
function applyTranslations(lang) {
    // Translate all elements with data-translate attribute
    document.querySelectorAll('[data-translate]').forEach(element => {
        const key = element.getAttribute('data-translate');
        element.textContent = translate(key, lang);
    });

    // Translate placeholders
    document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
        const key = element.getAttribute('data-translate-placeholder');
        element.placeholder = translate(key, lang);
    });

    // Translate titles
    document.querySelectorAll('[data-translate-title]').forEach(element => {
        const key = element.getAttribute('data-translate-title');
        element.title = translate(key, lang);
    });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { translations, translate, applyTranslations };
}
