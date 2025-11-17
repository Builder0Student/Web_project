import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DATABASE_NAME = 'arab_podcast.db'


def get_db():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with all required tables"""
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            bio TEXT,
            profile_image TEXT DEFAULT 'default-avatar.png',
            is_admin BOOLEAN DEFAULT 0,
            is_creator BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Podcasts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS podcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            audio_file TEXT NOT NULL,
            cover_image TEXT DEFAULT 'default-cover.jpg',
            duration INTEGER DEFAULT 0,
            category_id INTEGER,
            user_id INTEGER NOT NULL,
            plays INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Playlists table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            user_id INTEGER NOT NULL,
            is_public BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Playlist items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            podcast_id INTEGER NOT NULL,
            position INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (playlist_id) REFERENCES playlists (id) ON DELETE CASCADE,
            FOREIGN KEY (podcast_id) REFERENCES podcasts (id) ON DELETE CASCADE
        )
    ''')

    # Favorites table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            podcast_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (podcast_id) REFERENCES podcasts (id) ON DELETE CASCADE,
            UNIQUE(user_id, podcast_id)
        )
    ''')

    # Comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            podcast_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (podcast_id) REFERENCES podcasts (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # Listening history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listening_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            podcast_id INTEGER NOT NULL,
            progress INTEGER DEFAULT 0,
            last_position INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            last_listened TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (podcast_id) REFERENCES podcasts (id) ON DELETE CASCADE,
            UNIQUE(user_id, podcast_id)
        )
    ''')

    # Subscriptions table (users following other creators)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER NOT NULL,
            creator_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subscriber_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (creator_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(subscriber_id, creator_id)
        )
    ''')

    conn.commit()
    conn.close()


def seed_initial_data():
    """Seed database with initial data"""
    conn = get_db()
    cursor = conn.cursor()

    # Check if admin exists
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        # Create admin user
        admin_password = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (username, email, password, full_name, is_admin, is_creator)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@arabpodcast.com', admin_password, 'Administrator', 1, 1))

    # Check if categories exist
    cursor.execute('SELECT COUNT(*) as count FROM categories')
    if cursor.fetchone()['count'] == 0:
        categories = [
            ('Technology', 'Tech news, reviews, and discussions', 'fa-microchip'),
            ('Business', 'Entrepreneurship, finance, and business insights', 'fa-briefcase'),
            ('Education', 'Learning and educational content', 'fa-graduation-cap'),
            ('Entertainment', 'Movies, TV shows, and pop culture', 'fa-film'),
            ('Sports', 'Sports news, analysis, and commentary', 'fa-futbol'),
            ('Health', 'Health, fitness, and wellness', 'fa-heartbeat'),
            ('News', 'Current events and news analysis', 'fa-newspaper'),
            ('Comedy', 'Humor and comedy podcasts', 'fa-laugh'),
            ('History', 'Historical events and stories', 'fa-landmark'),
            ('Science', 'Scientific discoveries and discussions', 'fa-flask'),
            ('Arts', 'Art, design, and creativity', 'fa-palette'),
            ('Music', 'Music discussions and interviews', 'fa-music'),
        ]

        cursor.executemany('''
            INSERT INTO categories (name, description, icon)
            VALUES (?, ?, ?)
        ''', categories)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    print('Initializing database...')
    init_db()
    print('Database initialized successfully!')
    print('Seeding initial data...')
    seed_initial_data()
    print('Initial data seeded successfully!')
    print('\nDefault Admin Credentials:')
    print('Username: admin')
    print('Password: admin123')