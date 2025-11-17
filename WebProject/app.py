from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
from datetime import datetime
from database import get_db, init_db, seed_initial_data

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-to-random-secret-key-in-production'
app.config['UPLOAD_FOLDER'] = 'static/podcasts'
app.config['COVER_FOLDER'] = 'static/covers'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
app.config['ALLOWED_AUDIO_EXTENSIONS'] = {'mp3', 'wav', 'm4a', 'ogg'}
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['COVER_FOLDER'], exist_ok=True)


# Helper functions
def allowed_file(filename, file_type='audio'):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'audio':
        return ext in app.config['ALLOWED_AUDIO_EXTENSIONS']
    elif file_type == 'image':
        return ext in app.config['ALLOWED_IMAGE_EXTENSIONS']
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
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')

        if not all([username, email, password]):
            flash('All fields are required', 'error')
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

    # Get comments
    comments = conn.execute('''
        SELECT c.*, u.username, u.profile_image
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.podcast_id = ?
        ORDER BY c.created_at DESC
    ''', (podcast_id,)).fetchall()

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
                           related=related,
                           is_favorited=is_favorited,
                           user=get_current_user())


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        audio_file = request.files.get('audio_file')
        cover_image = request.files.get('cover_image')

        if not all([title, audio_file]):
            flash('Title and audio file are required', 'error')
            return redirect(url_for('upload'))

        if not allowed_file(audio_file.filename, 'audio'):
            flash('Invalid audio file format', 'error')
            return redirect(url_for('upload'))

        # Save audio file
        audio_filename = secure_filename(f"{datetime.now().timestamp()}_{audio_file.filename}")
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        audio_file.save(audio_path)

        # Save cover image if provided
        cover_filename = 'default-cover.jpg'
        if cover_image and allowed_file(cover_image.filename, 'image'):
            cover_filename = secure_filename(f"{datetime.now().timestamp()}_{cover_image.filename}")
            cover_path = os.path.join(app.config['COVER_FOLDER'], cover_filename)
            cover_image.save(cover_path)

        # Insert into database
        conn = get_db()
        conn.execute('''
            INSERT INTO podcasts (title, description, audio_file, cover_image, category_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, audio_filename, cover_filename, category_id, session['user_id']))
        conn.commit()
        conn.close()

        flash('Podcast uploaded successfully!', 'success')
        return redirect(url_for('profile', username=session['username']))

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

    if not content:
        return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400

    conn = get_db()
    conn.execute('''
        INSERT INTO comments (podcast_id, user_id, content)
        VALUES (?, ?, ?)
    ''', (podcast_id, session['user_id'], content))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Comment added successfully'})


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
    conn.execute('DELETE FROM podcasts WHERE id = ?', (podcast_id,))
    conn.commit()
    conn.close()

    flash('Podcast deleted successfully', 'success')
    return redirect(url_for('admin_podcasts'))


if __name__ == '__main__':
    init_db()
    seed_initial_data()
    app.run(debug=True, host='0.0.0.0', port=5000)