from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import re
from datetime import datetime
from database import get_db, init_db, seed_initial_data
from PIL import Image
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-to-random-secret-key-in-production'
app.config['UPLOAD_FOLDER'] = 'static/podcasts'
app.config['VIDEO_FOLDER'] = 'static/videos'
app.config['COVER_FOLDER'] = 'static/covers'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['ALLOWED_AUDIO_EXTENSIONS'] = {'mp3', 'wav', 'm4a', 'ogg'}
app.config['ALLOWED_VIDEO_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'}
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)
os.makedirs(app.config['COVER_FOLDER'], exist_ok=True)


# Helper functions
def allowed_file(filename, file_type='audio'):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'audio':
        return ext in app.config['ALLOWED_AUDIO_EXTENSIONS']
    elif file_type == 'video':
        return ext in app.config['ALLOWED_VIDEO_EXTENSIONS']
    elif file_type == 'image':
        return ext in app.config['ALLOWED_IMAGE_EXTENSIONS']
    return False


def resize_image_to_square(image_file, output_path, size=800):
    """
    Resize and crop image to a perfect square (1:1 ratio).
    Args:
        image_file: FileStorage object from Flask request.files
        output_path: Path where the resized image will be saved
        size: Target width and height in pixels (default 800x800)
    """
    try:
        # Open the image
        img = Image.open(image_file)

        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background

        # Get current dimensions
        width, height = img.size

        # Calculate the crop box to make it square (centered crop)
        if width > height:
            # Landscape - crop sides
            left = (width - height) // 2
            top = 0
            right = left + height
            bottom = height
        else:
            # Portrait or square - crop top/bottom
            left = 0
            top = (height - width) // 2
            right = width
            bottom = top + width

        # Crop to square
        img_cropped = img.crop((left, top, right, bottom))

        # Resize to target size with high-quality resampling
        img_resized = img_cropped.resize((size, size), Image.Resampling.LANCZOS)

        # Save with optimization
        img_resized.save(output_path, quality=90, optimize=True)

        return True
    except Exception as e:
        print(f"Error resizing image: {e}")
        return False


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))

        conn = get_db()
        user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()

        if not user or not user['is_admin']:
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    if 'user_id' in session:
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return user
    return None


# Routes
@app.route('/')
def index():
    conn = get_db()

    # Get trending podcasts
    trending = conn.execute('''
        SELECT p.*, u.username, u.full_name, c.name as category_name,
               (SELECT COUNT(*) FROM favorites WHERE podcast_id = p.id) as favorites_count
        FROM podcasts p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.plays DESC, p.created_at DESC
        LIMIT 12
    ''').fetchall()

    # Get recent podcasts
    recent = conn.execute('''
        SELECT p.*, u.username, u.full_name, c.name as category_name,
               (SELECT COUNT(*) FROM favorites WHERE podcast_id = p.id) as favorites_count
        FROM podcasts p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC
        LIMIT 12
    ''').fetchall()

    # Get categories with podcast count
    categories = conn.execute('''
        SELECT c.*, COUNT(p.id) as podcast_count
        FROM categories c
        LEFT JOIN podcasts p ON c.id = p.category_id
        GROUP BY c.id
        ORDER BY podcast_count DESC
        LIMIT 8
    ''').fetchall()

    conn.close()

    return render_template('index.html',
                           trending=trending,
                           recent=recent,
                           categories=categories,
                           user=get_current_user())


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        full_name = request.form.get('full_name', '').strip()

        # Validate required fields
        if not all([username, email, password]):
            flash('All required fields must be filled', 'error')
            return redirect(url_for('register'))

        # Validate username format (only letters, numbers, and underscores)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Username can only contain letters, numbers, and underscores', 'error')
            return redirect(url_for('register'))

        # Validate username length
        if len(username) < 3 or len(username) > 50:
            flash('Username must be between 3 and 50 characters', 'error')
            return redirect(url_for('register'))

        # Validate password length
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('register'))

        conn = get_db()

        # Check if username or email exists
        existing = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?',
                                (username, email)).fetchone()

        if existing:
            flash('Username or email already exists', 'error')
            conn.close()
            return redirect(url_for('register'))

        # Create user
        hashed_password = generate_password_hash(password)
        conn.execute('''
            INSERT INTO users (username, email, password, full_name)
            VALUES (?, ?, ?, ?)
        ''', (username, email, hashed_password, full_name))
        conn.commit()
        conn.close()

        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not all([username, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('login'))

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?',
                            (username, username)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            flash('Welcome back!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


@app.route('/browse')
def browse():
    conn = get_db()

    category_id = request.args.get('category')
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'recent')

    query = '''
        SELECT p.*, u.username, u.full_name, c.name as category_name,
               (SELECT COUNT(*) FROM favorites WHERE podcast_id = p.id) as favorites_count
        FROM podcasts p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    '''
    params = []

    if category_id:
        query += ' AND p.category_id = ?'
        params.append(category_id)

    if search_query:
        query += ' AND (p.title LIKE ? OR p.description LIKE ? OR u.username LIKE ?)'
        search_param = f'%{search_query}%'
        params.extend([search_param, search_param, search_param])

    if sort_by == 'recent':
        query += ' ORDER BY p.created_at DESC'
    elif sort_by == 'popular':
        query += ' ORDER BY p.plays DESC'
    elif sort_by == 'liked':
        query += ' ORDER BY favorites_count DESC'

    podcasts = conn.execute(query, params).fetchall()
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()

    conn.close()

    return render_template('browse.html',
                           podcasts=podcasts,
                           categories=categories,
                           selected_category=category_id,
                           search_query=search_query,
                           sort_by=sort_by,
                           user=get_current_user())


@app.route('/podcast/<int:podcast_id>')
def podcast_detail(podcast_id):
    conn = get_db()

    podcast = conn.execute('''
        SELECT p.*, u.username, u.full_name, u.bio, u.profile_image, c.name as category_name,
               (SELECT COUNT(*) FROM favorites WHERE podcast_id = p.id) as favorites_count
        FROM podcasts p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?
    ''', (podcast_id,)).fetchone()

    if not podcast:
        flash('Podcast not found', 'error')
        conn.close()
        return redirect(url_for('index'))

    # Get comments with likes info and user roles
    user_id = session.get('user_id')
    # Get top-level comments (parent comments only)
    comments_query = '''
        SELECT c.*, u.username, u.profile_image, u.is_admin, u.is_creator,
               (SELECT COUNT(*) FROM comment_likes WHERE comment_id = c.id) as likes_count,
               {} as is_liked_by_user,
               (SELECT COUNT(*) FROM comments WHERE parent_id = c.id) as replies_count
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.podcast_id = ? AND c.parent_id IS NULL
        ORDER BY c.is_pinned DESC, c.created_at DESC
    '''.format(
        f'(SELECT COUNT(*) FROM comment_likes WHERE comment_id = c.id AND user_id = {user_id}) > 0' if user_id else '0'
    )
    parent_comments = conn.execute(comments_query, (podcast_id,)).fetchall()

    # Get all replies for these comments
    replies_query = '''
        SELECT c.*, u.username, u.profile_image, u.is_admin, u.is_creator,
               (SELECT COUNT(*) FROM comment_likes WHERE comment_id = c.id) as likes_count,
               {} as is_liked_by_user
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.podcast_id = ? AND c.parent_id IS NOT NULL
        ORDER BY c.created_at ASC
    '''.format(
        f'(SELECT COUNT(*) FROM comment_likes WHERE comment_id = c.id AND user_id = {user_id}) > 0' if user_id else '0'
    )
    all_replies = conn.execute(replies_query, (podcast_id,)).fetchall()

    # Organize replies by parent_id
    replies_by_parent = {}
    for reply in all_replies:
        parent_id = reply['parent_id']
        if parent_id not in replies_by_parent:
            replies_by_parent[parent_id] = []
        replies_by_parent[parent_id].append(reply)

    comments = parent_comments

    # Get related podcasts
    related = conn.execute('''
        SELECT p.*, u.username, c.name as category_name
        FROM podcasts p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.category_id = ? AND p.id != ?
        ORDER BY RANDOM()
        LIMIT 6
    ''', (podcast['category_id'], podcast_id)).fetchall()

    # Check if user favorited
    is_favorited = False
    if 'user_id' in session:
        fav = conn.execute('''
            SELECT id FROM favorites WHERE user_id = ? AND podcast_id = ?
        ''', (session['user_id'], podcast_id)).fetchone()
        is_favorited = fav is not None

        # Update listening history
        conn.execute('''
            INSERT OR REPLACE INTO listening_history (user_id, podcast_id, last_listened)
            VALUES (?, ?, ?)
        ''', (session['user_id'], podcast_id, datetime.now()))
        conn.commit()

    # Increment play count
    conn.execute('UPDATE podcasts SET plays = plays + 1 WHERE id = ?', (podcast_id,))
    conn.commit()

    conn.close()

    return render_template('podcast_detail.html',
                           podcast=podcast,
                           comments=comments,
                           replies_by_parent=replies_by_parent,
                           related=related,
                           is_favorited=is_favorited,
                           user=get_current_user())


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            category_id = request.form.get('category_id')
            media_type = request.form.get('media_type', 'audio')  # 'audio' or 'video'
            media_file = request.files.get('audio_file')  # Name stays 'audio_file' for backward compatibility
            cover_image = request.files.get('cover_image')

            # Validate title
            if not title:
                flash('Content title is required', 'error')
                return redirect(url_for('upload'))

            if len(title) < 3:
                flash('Title must be at least 3 characters long', 'error')
                return redirect(url_for('upload'))

            # Validate category
            if not category_id:
                flash('Please select a category', 'error')
                return redirect(url_for('upload'))

            # Validate media file
            if not media_file or media_file.filename == '':
                flash('Media file is required', 'error')
                return redirect(url_for('upload'))

            # Validate file type based on media_type
            if media_type == 'video':
                if not allowed_file(media_file.filename, 'video'):
                    flash('Invalid video file format. Allowed formats: MP4, AVI, MOV, WMV, FLV, MKV, WEBM', 'error')
                    return redirect(url_for('upload'))
            else:
                if not allowed_file(media_file.filename, 'audio'):
                    flash('Invalid audio file format. Allowed formats: MP3, WAV, M4A, OGG', 'error')
                    return redirect(url_for('upload'))

            # Check media file size (max 500MB)
            media_file.seek(0, os.SEEK_END)
            media_size = media_file.tell()
            media_file.seek(0)

            if media_size > app.config['MAX_CONTENT_LENGTH']:
                flash('Media file is too large. Maximum size is 500MB', 'error')
                return redirect(url_for('upload'))

            if media_size == 0:
                flash('Media file is empty', 'error')
                return redirect(url_for('upload'))

            # Save media file to appropriate folder
            media_filename = secure_filename(f"{datetime.now().timestamp()}_{media_file.filename}")
            if media_type == 'video':
                media_path = os.path.join(app.config['VIDEO_FOLDER'], media_filename)
            else:
                media_path = os.path.join(app.config['UPLOAD_FOLDER'], media_filename)
            media_file.save(media_path)

            # Save cover image if provided
            cover_filename = 'default-cover.jpg'
            if cover_image and cover_image.filename != '':
                if not allowed_file(cover_image.filename, 'image'):
                    flash('Invalid cover image format. Allowed formats: PNG, JPG, JPEG, WEBP', 'error')
                    # Remove uploaded media file
                    if os.path.exists(media_path):
                        os.remove(media_path)
                    return redirect(url_for('upload'))

                # Generate filename and save with auto-resize to 1:1 ratio
                cover_filename = secure_filename(f"{datetime.now().timestamp()}_{cover_image.filename}")
                # Change extension to jpg for consistency
                cover_filename = os.path.splitext(cover_filename)[0] + '.jpg'
                cover_path = os.path.join(app.config['COVER_FOLDER'], cover_filename)

                # Resize image to perfect square (800x800)
                if not resize_image_to_square(cover_image, cover_path, size=800):
                    flash('Failed to process cover image', 'error')
                    # Remove uploaded media file
                    if os.path.exists(media_path):
                        os.remove(media_path)
                    return redirect(url_for('upload'))

            # Insert into database
            conn = get_db()
            conn.execute('''
                INSERT INTO podcasts (title, description, audio_file, cover_image, media_type, category_id, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, media_filename, cover_filename, media_type, category_id, session['user_id']))
            conn.commit()
            conn.close()

            flash('Content uploaded successfully!', 'success')
            return redirect(url_for('profile', username=session['username']))

        except Exception as e:
            flash(f'Upload failed: {str(e)}', 'error')
            # Clean up any uploaded files
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.remove(audio_path)
            if 'cover_path' in locals() and os.path.exists(cover_path):
                os.remove(cover_path)
            return redirect(url_for('upload'))

    conn = get_db()
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()

    return render_template('upload.html', categories=categories, user=get_current_user())


@app.route('/profile/<username>')
def profile(username):
    conn = get_db()

    user_profile = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

    if not user_profile:
        flash('User not found', 'error')
        conn.close()
        return redirect(url_for('index'))

    # Get user's podcasts
    podcasts = conn.execute('''
        SELECT p.*, c.name as category_name,
               (SELECT COUNT(*) FROM favorites WHERE podcast_id = p.id) as favorites_count
        FROM podcasts p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.user_id = ?
        ORDER BY p.created_at DESC
    ''', (user_profile['id'],)).fetchall()

    # Get user's playlists
    playlists = conn.execute('''
        SELECT pl.*, COUNT(pi.id) as podcast_count
        FROM playlists pl
        LEFT JOIN playlist_items pi ON pl.id = pi.playlist_id
        WHERE pl.user_id = ? AND (pl.is_public = 1 OR ? = ?)
        GROUP BY pl.id
        ORDER BY pl.created_at DESC
    ''', (user_profile['id'], session.get('user_id'), user_profile['id'])).fetchall()

    # Check if current user is subscribed
    is_subscribed = False
    if 'user_id' in session and session['user_id'] != user_profile['id']:
        sub = conn.execute('''
            SELECT id FROM subscriptions WHERE subscriber_id = ? AND creator_id = ?
        ''', (session['user_id'], user_profile['id'])).fetchone()
        is_subscribed = sub is not None

    # Get subscriber count
    subscriber_count = conn.execute('''
        SELECT COUNT(*) as count FROM subscriptions WHERE creator_id = ?
    ''', (user_profile['id'],)).fetchone()['count']

    conn.close()

    return render_template('profile.html',
                           user_profile=user_profile,
                           podcasts=podcasts,
                           playlists=playlists,
                           is_subscribed=is_subscribed,
                           subscriber_count=subscriber_count,
                           user=get_current_user())


@app.route('/library')
@login_required
def library():
    conn = get_db()

    # Get favorites
    favorites = conn.execute('''
        SELECT p.*, u.username, c.name as category_name
        FROM favorites f
        JOIN podcasts p ON f.podcast_id = p.id
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    ''', (session['user_id'],)).fetchall()

    # Get listening history
    history = conn.execute('''
        SELECT p.*, u.username, c.name as category_name, h.progress, h.last_position
        FROM listening_history h
        JOIN podcasts p ON h.podcast_id = p.id
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE h.user_id = ?
        ORDER BY h.last_listened DESC
        LIMIT 20
    ''', (session['user_id'],)).fetchall()

    # Get playlists
    playlists = conn.execute('''
        SELECT pl.*, COUNT(pi.id) as podcast_count
        FROM playlists pl
        LEFT JOIN playlist_items pi ON pl.id = pi.playlist_id
        WHERE pl.user_id = ?
        GROUP BY pl.id
        ORDER BY pl.created_at DESC
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return render_template('library.html',
                           favorites=favorites,
                           history=history,
                           playlists=playlists,
                           user=get_current_user())


@app.route('/playlist/<int:playlist_id>')
@login_required
def playlist_detail(playlist_id):
    conn = get_db()

    # Get playlist info
    playlist = conn.execute('''
        SELECT * FROM playlists WHERE id = ? AND user_id = ?
    ''', (playlist_id, session['user_id'])).fetchone()

    if not playlist:
        flash('Playlist not found', 'error')
        conn.close()
        return redirect(url_for('library'))

    # Get podcasts in the playlist
    podcasts = conn.execute('''
        SELECT p.*, u.username, c.name as category_name,
               (SELECT COUNT(*) FROM favorites WHERE podcast_id = p.id) as favorites_count
        FROM playlist_items pi
        JOIN podcasts p ON pi.podcast_id = p.id
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE pi.playlist_id = ?
        ORDER BY pi.added_at DESC
    ''', (playlist_id,)).fetchall()

    conn.close()

    return render_template('playlist_detail.html',
                           playlist=playlist,
                           podcasts=podcasts,
                           user=get_current_user())


# API Routes
@app.route('/api/favorite/<int:podcast_id>', methods=['POST'])
@login_required
def toggle_favorite(podcast_id):
    conn = get_db()

    existing = conn.execute('''
        SELECT id FROM favorites WHERE user_id = ? AND podcast_id = ?
    ''', (session['user_id'], podcast_id)).fetchone()

    if existing:
        conn.execute('DELETE FROM favorites WHERE id = ?', (existing['id'],))
        is_favorited = False
    else:
        conn.execute('''
            INSERT INTO favorites (user_id, podcast_id) VALUES (?, ?)
        ''', (session['user_id'], podcast_id))
        is_favorited = True

    conn.commit()

    # Get new count
    count = conn.execute('''
        SELECT COUNT(*) as count FROM favorites WHERE podcast_id = ?
    ''', (podcast_id,)).fetchone()['count']

    conn.close()

    return jsonify({'success': True, 'is_favorited': is_favorited, 'count': count})


@app.route('/api/comment/<int:podcast_id>', methods=['POST'])
@login_required
def add_comment(podcast_id):
    content = request.json.get('content')
    parent_id = request.json.get('parent_id')  # Optional: for replies

    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400

    conn = get_db()
    conn.execute('''
        INSERT INTO comments (podcast_id, user_id, content, parent_id)
        VALUES (?, ?, ?, ?)
    ''', (podcast_id, session['user_id'], content, parent_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Comment added successfully'})


@app.route('/api/comment/<int:comment_id>/like', methods=['POST'])
@login_required
def toggle_comment_like(comment_id):
    conn = get_db()

    existing = conn.execute('''
        SELECT id FROM comment_likes WHERE comment_id = ? AND user_id = ?
    ''', (comment_id, session['user_id'])).fetchone()

    if existing:
        # Unlike
        conn.execute('DELETE FROM comment_likes WHERE comment_id = ? AND user_id = ?',
                    (comment_id, session['user_id']))
        is_liked = False
    else:
        # Like
        conn.execute('INSERT INTO comment_likes (comment_id, user_id) VALUES (?, ?)',
                    (comment_id, session['user_id']))
        is_liked = True

    # Get updated like count
    likes_count = conn.execute('''
        SELECT COUNT(*) as count FROM comment_likes WHERE comment_id = ?
    ''', (comment_id,)).fetchone()['count']

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'is_liked': is_liked, 'likes_count': likes_count})


@app.route('/api/comment/<int:comment_id>/pin', methods=['POST'])
@login_required
def toggle_pin_comment(comment_id):
    conn = get_db()

    # Get the comment and podcast details
    comment = conn.execute('''
        SELECT c.*, p.user_id as podcast_creator_id
        FROM comments c
        JOIN podcasts p ON c.podcast_id = p.id
        WHERE c.id = ?
    ''', (comment_id,)).fetchone()

    if not comment:
        conn.close()
        return jsonify({'success': False, 'message': 'Comment not found'}), 404

    # Check if user is the podcast creator
    if comment['podcast_creator_id'] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Only podcast creator can pin comments'}), 403

    # Toggle pin status
    new_pin_status = 0 if comment['is_pinned'] else 1

    # If pinning, unpin all other comments on this podcast first
    if new_pin_status == 1:
        conn.execute('''
            UPDATE comments SET is_pinned = 0
            WHERE podcast_id = ? AND id != ?
        ''', (comment['podcast_id'], comment_id))

    # Update this comment's pin status
    conn.execute('UPDATE comments SET is_pinned = ? WHERE id = ?',
                (new_pin_status, comment_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'is_pinned': bool(new_pin_status)})


@app.route('/api/comment/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    conn = get_db()

    # Get the comment and podcast details
    comment = conn.execute('''
        SELECT c.*, p.user_id as podcast_creator_id
        FROM comments c
        JOIN podcasts p ON c.podcast_id = p.id
        WHERE c.id = ?
    ''', (comment_id,)).fetchone()

    if not comment:
        conn.close()
        return jsonify({'success': False, 'message': 'Comment not found'}), 404

    # Check if user is the comment author or podcast creator
    if comment['user_id'] != session['user_id'] and comment['podcast_creator_id'] != session['user_id']:
        conn.close()
        return jsonify({'success': False, 'message': 'You can only delete your own comments or comments on your podcast'}), 403

    # Delete the comment (cascade will delete associated likes)
    conn.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Comment deleted successfully'})


@app.route('/api/subscribe/<int:creator_id>', methods=['POST'])
@login_required
def toggle_subscribe(creator_id):
    if session['user_id'] == creator_id:
        return jsonify({'success': False, 'message': 'Cannot subscribe to yourself'}), 400

    conn = get_db()

    existing = conn.execute('''
        SELECT id FROM subscriptions WHERE subscriber_id = ? AND creator_id = ?
    ''', (session['user_id'], creator_id)).fetchone()

    if existing:
        conn.execute('DELETE FROM subscriptions WHERE id = ?', (existing['id'],))
        is_subscribed = False
    else:
        conn.execute('''
            INSERT INTO subscriptions (subscriber_id, creator_id) VALUES (?, ?)
        ''', (session['user_id'], creator_id))
        is_subscribed = True

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'is_subscribed': is_subscribed})


# Playlist API Routes
@app.route('/api/playlists', methods=['GET'])
@login_required
def api_get_playlists():
    conn = get_db()

    playlists = conn.execute('''
        SELECT p.*, COUNT(pi.id) as item_count
        FROM playlists p
        LEFT JOIN playlist_items pi ON p.id = pi.playlist_id
        WHERE p.user_id = ?
        GROUP BY p.id
        ORDER BY p.created_at DESC
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return jsonify({
        'success': True,
        'playlists': [dict(playlist) for playlist in playlists]
    })


@app.route('/api/playlists/create', methods=['POST'])
@login_required
def api_create_playlist():
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not name:
        return jsonify({'success': False, 'message': 'Playlist name is required'}), 400

    conn = get_db()

    try:
        conn.execute('''
            INSERT INTO playlists (name, description, user_id)
            VALUES (?, ?, ?)
        ''', (name, description, session['user_id']))
        conn.commit()

        playlist_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'message': 'Playlist created successfully',
            'playlist_id': playlist_id
        })

    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/playlists/<int:playlist_id>/add', methods=['POST'])
@login_required
def api_add_to_playlist(playlist_id):
    data = request.get_json()
    podcast_id = data.get('podcast_id')

    if not podcast_id:
        return jsonify({'success': False, 'message': 'Podcast ID is required'}), 400

    conn = get_db()

    # Verify playlist belongs to user
    playlist = conn.execute('''
        SELECT id FROM playlists WHERE id = ? AND user_id = ?
    ''', (playlist_id, session['user_id'])).fetchone()

    if not playlist:
        conn.close()
        return jsonify({'success': False, 'message': 'Playlist not found'}), 404

    # Check if podcast already in playlist
    existing = conn.execute('''
        SELECT id FROM playlist_items WHERE playlist_id = ? AND podcast_id = ?
    ''', (playlist_id, podcast_id)).fetchone()

    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Podcast already in playlist'}), 400

    try:
        conn.execute('''
            INSERT INTO playlist_items (playlist_id, podcast_id)
            VALUES (?, ?)
        ''', (playlist_id, podcast_id))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Podcast added to playlist successfully'
        })

    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()

    # Get statistics
    stats = {
        'total_users': conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count'],
        'total_podcasts': conn.execute('SELECT COUNT(*) as count FROM podcasts').fetchone()['count'],
        'total_plays': conn.execute('SELECT SUM(plays) as total FROM podcasts').fetchone()['total'] or 0,
        'total_comments': conn.execute('SELECT COUNT(*) as count FROM comments').fetchone()['count']
    }

    # Get recent podcasts
    recent_podcasts = conn.execute('''
        SELECT p.*, u.username FROM podcasts p
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        LIMIT 10
    ''').fetchall()

    # Get recent users
    recent_users = conn.execute('''
        SELECT * FROM users ORDER BY created_at DESC LIMIT 10
    ''').fetchall()

    conn.close()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_podcasts=recent_podcasts,
                           recent_users=recent_users,
                           user=get_current_user())


@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    conn = get_db()

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon')

        conn.execute('''
            INSERT INTO categories (name, description, icon)
            VALUES (?, ?, ?)
        ''', (name, description, icon))
        conn.commit()
        flash('Category added successfully', 'success')

    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()

    return render_template('admin/categories.html',
                           categories=categories,
                           user=get_current_user())


@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
    conn.close()

    return render_template('admin/users.html', users=users, user=get_current_user())


@app.route('/admin/podcasts')
@admin_required
def admin_podcasts():
    conn = get_db()
    podcasts = conn.execute('''
        SELECT p.*, u.username, c.name as category_name
        FROM podcasts p
        LEFT JOIN users u ON p.user_id = u.id
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    conn.close()

    return render_template('admin/podcasts.html', podcasts=podcasts, user=get_current_user())


@app.route('/admin/delete/podcast/<int:podcast_id>', methods=['POST'])
@admin_required
def admin_delete_podcast(podcast_id):
    conn = get_db()

    # Get podcast info before deleting
    podcast = conn.execute('SELECT * FROM podcasts WHERE id = ?', (podcast_id,)).fetchone()

    if podcast:
        # Delete podcast from database
        conn.execute('DELETE FROM podcasts WHERE id = ?', (podcast_id,))
        conn.commit()

        # Delete associated files
        try:
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], podcast['audio_file'])
            if os.path.exists(audio_path):
                os.remove(audio_path)

            if podcast['cover_image'] != 'default-cover.jpg':
                cover_path = os.path.join(app.config['COVER_FOLDER'], podcast['cover_image'])
                if os.path.exists(cover_path):
                    os.remove(cover_path)
        except Exception as e:
            print(f"Error deleting files: {e}")

    conn.close()
    flash('Podcast deleted successfully', 'success')
    return redirect(url_for('admin_podcasts'))


@app.route('/admin/user/toggle-admin/<int:user_id>', methods=['POST'])
@admin_required
def admin_toggle_admin(user_id):
    # Prevent removing admin from yourself
    if user_id == session['user_id']:
        flash('You cannot change your own admin status', 'error')
        return redirect(url_for('admin_users'))

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user:
        new_admin_status = 0 if user['is_admin'] else 1
        conn.execute('UPDATE users SET is_admin = ? WHERE id = ?', (new_admin_status, user_id))
        conn.commit()

        status = 'Admin' if new_admin_status else 'User'
        flash(f'User {user["username"]} is now a {status}', 'success')

    conn.close()
    return redirect(url_for('admin_users'))


@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    # Prevent deleting yourself
    if user_id == session['user_id']:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user:
        # Delete user's podcasts first
        podcasts = conn.execute('SELECT * FROM podcasts WHERE user_id = ?', (user_id,)).fetchall()
        for podcast in podcasts:
            try:
                audio_path = os.path.join(app.config['UPLOAD_FOLDER'], podcast['audio_file'])
                if os.path.exists(audio_path):
                    os.remove(audio_path)

                if podcast['cover_image'] != 'default-cover.jpg':
                    cover_path = os.path.join(app.config['COVER_FOLDER'], podcast['cover_image'])
                    if os.path.exists(cover_path):
                        os.remove(cover_path)
            except Exception as e:
                print(f"Error deleting podcast files: {e}")

        # Delete user and all associated data (cascade should handle this)
        conn.execute('DELETE FROM podcasts WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM favorites WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM playlists WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM subscriptions WHERE subscriber_id = ? OR creator_id = ?', (user_id, user_id))
        conn.execute('DELETE FROM listening_history WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()

        flash(f'User {user["username"]} and all their data have been deleted', 'success')

    conn.close()
    return redirect(url_for('admin_users'))


@app.route('/admin/user/edit/<int:user_id>', methods=['POST'])
@admin_required
def admin_edit_user(user_id):
    new_username = request.form.get('username', '').strip()

    if not new_username:
        flash('Username cannot be empty', 'error')
        return redirect(url_for('admin_users'))

    # Validate username format
    if not re.match(r'^[a-zA-Z0-9_]+$', new_username):
        flash('Username can only contain letters, numbers, and underscores', 'error')
        return redirect(url_for('admin_users'))

    conn = get_db()

    # Check if username already exists
    existing = conn.execute('SELECT id FROM users WHERE username = ? AND id != ?',
                           (new_username, user_id)).fetchone()

    if existing:
        flash('Username already exists', 'error')
        conn.close()
        return redirect(url_for('admin_users'))

    # Update username
    conn.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
    conn.commit()
    conn.close()

    flash('Username updated successfully', 'success')
    return redirect(url_for('admin_users'))


if __name__ == '__main__':
    init_db()
    seed_initial_data()
    app.run(debug=True, host='0.0.0.0', port=5000)