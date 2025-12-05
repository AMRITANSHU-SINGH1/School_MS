# ==================== ADD THESE MODELS TO YOUR app.py (after existing models) ====================

class UserProfile(db.Model):
    """Extended profile for Students, Teachers, and Alumni"""
    __tablename__ = 'user_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), unique=True, nullable=False)  # student_id, teacher_id, or alumni_id
    user_type = db.Column(db.String(20), nullable=False)  # 'student', 'teacher', 'alumni'
    
    # Profile Information
    bio = db.Column(db.Text)
    headline = db.Column(db.String(200))  # Professional headline
    profile_picture = db.Column(db.String(300))
    cover_photo = db.Column(db.String(300))
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    linkedin_url = db.Column(db.String(200))
    github_url = db.Column(db.String(200))
    
    # Privacy settings
    is_profile_public = db.Column(db.Boolean, default=True)
    show_email = db.Column(db.Boolean, default=False)
    show_phone = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    achievements = db.relationship('Achievement', backref='profile', lazy=True, cascade='all, delete-orphan')
    skills = db.relationship('Skill', backref='profile', lazy=True, cascade='all, delete-orphan')
    experiences = db.relationship('Experience', backref='profile', lazy=True, cascade='all, delete-orphan')
    hobbies = db.relationship('Hobby', backref='profile', lazy=True, cascade='all, delete-orphan')


class Alumni(db.Model):
    """Alumni who have graduated"""
    __tablename__ = 'alumni'
    id = db.Column(db.Integer, primary_key=True)
    alumni_id = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Alumni specific info
    graduation_year = db.Column(db.Integer, nullable=False)
    degree = db.Column(db.String(100))
    major = db.Column(db.String(100))
    current_company = db.Column(db.String(200))
    current_position = db.Column(db.String(200))
    
    phone = db.Column(db.String(15))
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Achievement(db.Model):
    """Achievements and awards"""
    __tablename__ = 'achievement'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # Academic, Sports, Cultural, Professional, etc.
    date_achieved = db.Column(db.Date)
    issuer = db.Column(db.String(200))  # Organization/Institution that issued
    certificate_url = db.Column(db.String(300))
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Skill(db.Model):
    """Skills and expertise"""
    __tablename__ = 'skill'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    proficiency = db.Column(db.String(20))  # Beginner, Intermediate, Advanced, Expert
    category = db.Column(db.String(50))  # Technical, Soft Skills, Languages, etc.
    
    endorsements = db.relationship('SkillEndorsement', backref='skill', lazy=True, cascade='all, delete-orphan')


class SkillEndorsement(db.Model):
    """Skill endorsements from other users"""
    __tablename__ = 'skill_endorsement'
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skill.id'), nullable=False)
    endorser_id = db.Column(db.String(20), nullable=False)  # user_id who endorsed
    endorser_type = db.Column(db.String(20), nullable=False)  # student, teacher, alumni
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.UniqueConstraint('skill_id', 'endorser_id', name='unique_endorsement'),
    )


class Experience(db.Model):
    """Work experience or internships"""
    __tablename__ = 'experience'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # NULL means currently working
    is_current = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Hobby(db.Model):
    """Hobbies and interests"""
    __tablename__ = 'hobby'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profile.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # Sports, Arts, Music, Reading, etc.


class Connection(db.Model):
    """Network connections between users"""
    __tablename__ = 'connection'
    id = db.Column(db.Integer, primary_key=True)
    
    requester_id = db.Column(db.String(20), nullable=False)  # Who sent the request
    requester_type = db.Column(db.String(20), nullable=False)
    
    receiver_id = db.Column(db.String(20), nullable=False)  # Who received the request
    receiver_type = db.Column(db.String(20), nullable=False)
    
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    message = db.Column(db.Text)  # Optional connection message
    
    requested_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    responded_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('requester_id', 'receiver_id', name='unique_connection'),
    )


class Post(db.Model):
    """Social posts/updates"""
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    
    author_id = db.Column(db.String(20), nullable=False)
    author_type = db.Column(db.String(20), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(300))
    
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    likes = db.relationship('PostLike', backref='post', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('PostComment', backref='post', lazy=True, cascade='all, delete-orphan')


class PostLike(db.Model):
    """Likes on posts"""
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    user_id = db.Column(db.String(20), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='unique_like'),
    )


class PostComment(db.Model):
    """Comments on posts"""
    __tablename__ = 'post_comment'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    
    author_id = db.Column(db.String(20), nullable=False)
    author_type = db.Column(db.String(20), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ==================== HELPER FUNCTIONS ====================

def get_user_info(user_id, user_type):
    """Get basic user information"""
    if user_type == 'student':
        user = Student.query.filter_by(student_id=user_id).first()
        return {'name': user.name, 'email': user.email, 'id': user.student_id} if user else None
    elif user_type == 'teacher':
        user = Teacher.query.filter_by(teacher_id=user_id).first()
        return {'name': user.name, 'email': user.email, 'id': user.teacher_id} if user else None
    elif user_type == 'alumni':
        user = Alumni.query.filter_by(alumni_id=user_id).first()
        return {'name': user.name, 'email': user.email, 'id': user.alumni_id} if user else None
    return None


def get_user_profile(user_id, user_type):
    """Get or create user profile"""
    profile = UserProfile.query.filter_by(user_id=user_id, user_type=user_type).first()
    if not profile:
        profile = UserProfile(user_id=user_id, user_type=user_type)
        db.session.add(profile)
        db.session.commit()
    return profile


def get_current_user():
    """Get current logged-in user info"""
    user_type = session.get('user_type')
    if user_type == 'student':
        user = Student.query.get(session.get('student_id'))
        return {'id': user.student_id, 'type': 'student', 'name': user.name, 'email': user.email} if user else None
    elif user_type == 'teacher':
        user = Teacher.query.filter_by(teacher_id=session.get('teacher_id')).first()
        return {'id': user.teacher_id, 'type': 'teacher', 'name': user.name, 'email': user.email} if user else None
    elif user_type == 'alumni':
        user = Alumni.query.filter_by(alumni_id=session.get('alumni_id')).first()
        return {'id': user.alumni_id, 'type': 'alumni', 'name': user.name, 'email': user.email} if user else None
    return None


def are_connected(user1_id, user2_id):
    """Check if two users are connected"""
    connection = Connection.query.filter(
        ((Connection.requester_id == user1_id) & (Connection.receiver_id == user2_id)) |
        ((Connection.requester_id == user2_id) & (Connection.receiver_id == user1_id))
    ).first()
    return connection and connection.status == 'accepted'


# ==================== AUTHENTICATION DECORATOR ====================

def social_login_required(f):
    """Decorator for routes that require any user login (student, teacher, or alumni)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== ALUMNI LOGIN ROUTES ====================

@app.route('/alumni/register', methods=['GET', 'POST'])
def alumni_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        graduation_year = int(request.form['graduation_year'])
        degree = request.form.get('degree', '')
        major = request.form.get('major', '')
        phone = request.form.get('phone', '')
        
        existing = Alumni.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'error')
            return redirect(url_for('alumni_register'))
        
        new_alumni = Alumni(
            name=name,
            email=email,
            graduation_year=graduation_year,
            degree=degree,
            major=major,
            phone=phone
        )
        new_alumni.set_password(password)
        db.session.add(new_alumni)
        db.session.commit()
        
        new_alumni.alumni_id = f'ALM_{new_alumni.id:03d}'
        db.session.commit()
        
        # Create profile
        get_user_profile(new_alumni.alumni_id, 'alumni')
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('alumni_login'))
    
    return render_template('alumni_register.html')


@app.route('/alumni/login', methods=['GET', 'POST'])
def alumni_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        alumni = Alumni.query.filter_by(email=email).first()
        
        if alumni and alumni.check_password(password):
            session['alumni_id'] = alumni.alumni_id
            session['user_type'] = 'alumni'
            flash('Login successful!', 'success')
            return redirect(url_for('social_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('alumni_login.html')


# ==================== SOCIAL DASHBOARD ====================

@app.route('/social/dashboard')
@social_login_required
def social_dashboard():
    """Main social networking dashboard"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    # Get connection stats
    connections_count = Connection.query.filter(
        ((Connection.requester_id == current['id']) | (Connection.receiver_id == current['id'])) &
        (Connection.status == 'accepted')
    ).count()
    
    pending_requests = Connection.query.filter_by(
        receiver_id=current['id'],
        status='pending'
    ).count()
    
    # Get recent posts from connections
    my_connections = Connection.query.filter(
        ((Connection.requester_id == current['id']) | (Connection.receiver_id == current['id'])) &
        (Connection.status == 'accepted')
    ).all()
    
    connection_ids = []
    for conn in my_connections:
        if conn.requester_id == current['id']:
            connection_ids.append(conn.receiver_id)
        else:
            connection_ids.append(conn.requester_id)
    
    # Include own posts
    connection_ids.append(current['id'])
    
    recent_posts = Post.query.filter(Post.author_id.in_(connection_ids)).order_by(Post.created_at.desc()).limit(20).all()
    
    # Add author info to posts
    for post in recent_posts:
        post.author_info = get_user_info(post.author_id, post.author_type)
        post.has_liked = PostLike.query.filter_by(post_id=post.id, user_id=current['id']).first() is not None
    
    stats = {
        'connections': connections_count,
        'pending_requests': pending_requests,
        'achievements': len(profile.achievements),
        'skills': len(profile.skills)
    }
    
    return render_template('social_dashboard.html',
                         current_user=current,
                         profile=profile,
                         stats=stats,
                         posts=recent_posts)


# ==================== PROFILE MANAGEMENT ====================

@app.route('/social/profile')
@social_login_required
def my_profile():
    """View own profile"""
    current = get_current_user()
    return redirect(url_for('view_profile', user_id=current['id'], user_type=current['type']))


@app.route('/social/profile/<user_type>/<user_id>')
@social_login_required
def view_profile(user_type, user_id):
    """View any user's profile"""
    current = get_current_user()
    
    # Get profile owner info
    owner = get_user_info(user_id, user_type)
    if not owner:
        flash('User not found', 'error')
        return redirect(url_for('social_dashboard'))
    
    profile = get_user_profile(user_id, user_type)
    
    # Check if viewing own profile
    is_own_profile = (current['id'] == user_id and current['type'] == user_type)
    
    # Check connection status
    connection_status = None
    if not is_own_profile:
        conn = Connection.query.filter(
            ((Connection.requester_id == current['id']) & (Connection.receiver_id == user_id)) |
            ((Connection.requester_id == user_id) & (Connection.receiver_id == current['id']))
        ).first()
        
        if conn:
            if conn.status == 'accepted':
                connection_status = 'connected'
            elif conn.requester_id == current['id']:
                connection_status = 'pending_sent'
            else:
                connection_status = 'pending_received'
    
    # Get connections count
    connections_count = Connection.query.filter(
        ((Connection.requester_id == user_id) | (Connection.receiver_id == user_id)) &
        (Connection.status == 'accepted')
    ).count()
    
    # Get user's posts
    user_posts = Post.query.filter_by(author_id=user_id, author_type=user_type).order_by(Post.created_at.desc()).limit(10).all()
    for post in user_posts:
        post.author_info = owner
        post.has_liked = PostLike.query.filter_by(post_id=post.id, user_id=current['id']).first() is not None
    
    return render_template('view_profile.html',
                         current_user=current,
                         owner=owner,
                         profile=profile,
                         is_own_profile=is_own_profile,
                         connection_status=connection_status,
                         connections_count=connections_count,
                         posts=user_posts)


@app.route('/social/profile/edit', methods=['GET', 'POST'])
@social_login_required
def edit_profile():
    """Edit own profile"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        profile.bio = request.form.get('bio', '')
        profile.headline = request.form.get('headline', '')
        profile.location = request.form.get('location', '')
        profile.website = request.form.get('website', '')
        profile.linkedin_url = request.form.get('linkedin_url', '')
        profile.github_url = request.form.get('github_url', '')
        
        profile.is_profile_public = 'is_profile_public' in request.form
        profile.show_email = 'show_email' in request.form
        profile.show_phone = 'show_phone' in request.form
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"profile_{current['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                profile.profile_picture = filepath
        
        profile.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_profile.html', current_user=current, profile=profile)


# Continue in next artifact...


# ==================== POST MANAGEMENT ====================

@app.route('/social/post/create', methods=['GET', 'POST'])
@social_login_required
def create_post():
    """Create a new post"""
    current = get_current_user()
    
    if request.method == 'POST':
        content = request.form['content']
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"post_{current['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                image_path = filepath
        
        new_post = Post(
            author_id=current['id'],
            author_type=current['type'],
            content=content,
            image_path=image_path
        )
        
        db.session.add(new_post)
        db.session.commit()
        
        flash('Post created successfully!', 'success')
        return redirect(url_for('social_dashboard'))
    
    return render_template('create_post.html', current_user=current)


@app.route('/social/post/<int:post_id>')
@social_login_required
def view_post(post_id):
    """View single post with comments"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    # Get author info
    post.author_info = get_user_info(post.author_id, post.author_type)
    post.has_liked = PostLike.query.filter_by(post_id=post.id, user_id=current['id']).first() is not None
    
    # Get comments with author info
    comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.created_at.desc()).all()
    for comment in comments:
        comment.author_info = get_user_info(comment.author_id, comment.author_type)
    
    return render_template('view_post.html',
                         current_user=current,
                         post=post,
                         comments=comments)


@app.route('/social/post/<int:post_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_post(post_id):
    """Edit a post"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    # Check ownership
    if post.author_id != current['id'] or post.author_type != current['type']:
        flash('Unauthorized', 'error')
        return redirect(url_for('social_dashboard'))
    
    if request.method == 'POST':
        post.content = request.form['content']
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"post_{current['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posts', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                
                # Delete old image if exists
                if post.image_path and os.path.exists(post.image_path):
                    os.remove(post.image_path)
                
                post.image_path = filepath
        
        post.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        flash('Post updated!', 'success')
        return redirect(url_for('view_post', post_id=post_id))
    
    return render_template('edit_post.html', current_user=current, post=post)


@app.route('/social/post/<int:post_id>/delete', methods=['POST'])
@social_login_required
def delete_post(post_id):
    """Delete a post"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    # Check ownership
    if post.author_id != current['id'] or post.author_type != current['type']:
        flash('Unauthorized', 'error')
        return redirect(url_for('social_dashboard'))
    
    # Delete image if exists
    if post.image_path and os.path.exists(post.image_path):
        os.remove(post.image_path)
    
    db.session.delete(post)
    db.session.commit()
    
    flash('Post deleted', 'info')
    return redirect(url_for('social_dashboard'))


@app.route('/social/post/<int:post_id>/like', methods=['POST'])
@social_login_required
def like_post(post_id):
    """Like/unlike a post"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    # Check if already liked
    existing_like = PostLike.query.filter_by(post_id=post_id, user_id=current['id']).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        post.likes_count = max(0, post.likes_count - 1)
        action = 'unliked'
    else:
        # Like
        new_like = PostLike(
            post_id=post_id,
            user_id=current['id'],
            user_type=current['type']
        )
        db.session.add(new_like)
        post.likes_count += 1
        action = 'liked'
    
    db.session.commit()
    
    # Return JSON for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'action': action,
            'likes_count': post.likes_count
        })
    
    return redirect(request.referrer or url_for('social_dashboard'))


@app.route('/social/post/<int:post_id>/comment', methods=['POST'])
@social_login_required
def comment_post(post_id):
    """Add a comment to a post"""
    current = get_current_user()
    post = Post.query.get_or_404(post_id)
    
    content = request.form['content']
    
    if not content.strip():
        flash('Comment cannot be empty', 'error')
        return redirect(request.referrer or url_for('view_post', post_id=post_id))
    
    new_comment = PostComment(
        post_id=post_id,
        author_id=current['id'],
        author_type=current['type'],
        content=content
    )
    
    db.session.add(new_comment)
    post.comments_count += 1
    db.session.commit()
    
    flash('Comment added!', 'success')
    return redirect(request.referrer or url_for('view_post', post_id=post_id))


@app.route('/social/comment/<int:comment_id>/delete', methods=['POST'])
@social_login_required
def delete_comment(comment_id):
    """Delete a comment"""
    current = get_current_user()
    comment = PostComment.query.get_or_404(comment_id)
    
    # Check ownership
    if comment.author_id != current['id'] or comment.author_type != current['type']:
        flash('Unauthorized', 'error')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    post = comment.post
    post.comments_count = max(0, post.comments_count - 1)
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted', 'info')
    return redirect(request.referrer or url_for('view_post', post_id=post.id))


# ==================== DISCOVER & SUGGESTIONS ====================

@app.route('/social/discover')
@social_login_required
def discover():
    """Discover new people to connect with"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    # Get users with similar skills
    my_skills = [s.name.lower() for s in profile.skills]
    
    suggestions = []
    
    # Get all profiles with skills
    all_profiles = UserProfile.query.filter(
        UserProfile.user_id != current['id']
    ).limit(50).all()
    
    for p in all_profiles:
        # Skip if already connected
        if are_connected(current['id'], p.user_id):
            continue
        
        # Check for pending connection
        conn = Connection.query.filter(
            ((Connection.requester_id == current['id']) & (Connection.receiver_id == p.user_id)) |
            ((Connection.requester_id == p.user_id) & (Connection.receiver_id == current['id']))
        ).first()
        
        if conn:
            continue
        
        # Calculate match score
        their_skills = [s.name.lower() for s in p.skills]
        common_skills = set(my_skills) & set(their_skills)
        
        if len(common_skills) > 0 or len(suggestions) < 20:
            user_info = get_user_info(p.user_id, p.user_type)
            if user_info:
                suggestions.append({
                    'user': user_info,
                    'type': p.user_type,
                    'profile': p,
                    'common_skills': list(common_skills),
                    'match_score': len(common_skills)
                })
    
    # Sort by match score
    suggestions.sort(key=lambda x: x['match_score'], reverse=True)
    
    return render_template('discover.html',
                         current_user=current,
                         suggestions=suggestions[:20])


# ==================== ALUMNI SPECIFIC ====================

@app.route('/social/alumni')
@social_login_required
def alumni_directory():
    """Browse alumni directory"""
    current = get_current_user()
    
    # Filters
    graduation_year = request.args.get('year', type=int)
    company = request.args.get('company', '')
    
    query = Alumni.query
    
    if graduation_year:
        query = query.filter_by(graduation_year=graduation_year)
    if company:
        query = query.filter(Alumni.current_company.ilike(f'%{company}%'))
    
    alumni_list = query.order_by(Alumni.graduation_year.desc()).all()
    
    # Get unique graduation years for filter
    years = db.session.query(Alumni.graduation_year).distinct().order_by(Alumni.graduation_year.desc()).all()
    years = [y[0] for y in years]
    
    # Add profile and connection info
    alumni_data = []
    for alumni in alumni_list:
        profile = get_user_profile(alumni.alumni_id, 'alumni')
        
        # Check connection status
        connection_status = None
        if alumni.alumni_id != current['id']:
            conn = Connection.query.filter(
                ((Connection.requester_id == current['id']) & (Connection.receiver_id == alumni.alumni_id)) |
                ((Connection.requester_id == alumni.alumni_id) & (Connection.receiver_id == current['id']))
            ).first()
            
            if conn:
                if conn.status == 'accepted':
                    connection_status = 'connected'
                elif conn.requester_id == current['id']:
                    connection_status = 'pending_sent'
                else:
                    connection_status = 'pending_received'
        
        alumni_data.append({
            'alumni': alumni,
            'profile': profile,
            'connection_status': connection_status
        })
    
    return render_template('alumni_directory.html',
                         current_user=current,
                         alumni_list=alumni_data,
                         years=years,
                         selected_year=graduation_year,
                         company_filter=company)


# ==================== NOTIFICATIONS ====================

@app.route('/social/notifications')
@social_login_required
def social_notifications():
    """View social notifications"""
    current = get_current_user()
    
    # Get connection requests
    connection_requests = Connection.query.filter_by(
        receiver_id=current['id'],
        status='pending'
    ).order_by(Connection.requested_at.desc()).all()
    
    notifications = []
    
    for req in connection_requests:
        user_info = get_user_info(req.requester_id, req.requester_type)
        notifications.append({
            'type': 'connection_request',
            'user': user_info,
            'user_type': req.requester_type,
            'connection': req,
            'time': req.requested_at
        })
    
    # Get recent endorsements
    my_profile = get_user_profile(current['id'], current['type'])
    recent_endorsements = []
    
    for skill in my_profile.skills:
        for endorsement in skill.endorsements:
            endorser_info = get_user_info(endorsement.endorser_id, endorsement.endorser_type)
            recent_endorsements.append({
                'type': 'skill_endorsement',
                'user': endorser_info,
                'skill': skill.name,
                'time': endorsement.created_at
            })
    
    # Sort by time and limit
    recent_endorsements.sort(key=lambda x: x['time'], reverse=True)
    notifications.extend(recent_endorsements[:10])
    
    # Sort all notifications by time
    notifications.sort(key=lambda x: x['time'], reverse=True)
    
    return render_template('social_notifications.html',
                         current_user=current,
                         notifications=notifications)


# ==================== API ENDPOINTS ====================

@app.route('/api/social/check_connection/<user_type>/<user_id>')
@social_login_required
def api_check_connection(user_type, user_id):
    """API to check connection status"""
    current = get_current_user()
    
    conn = Connection.query.filter(
        ((Connection.requester_id == current['id']) & (Connection.receiver_id == user_id)) |
        ((Connection.requester_id == user_id) & (Connection.receiver_id == current['id']))
    ).first()
    
    if not conn:
        return jsonify({'status': 'not_connected'})
    
    if conn.status == 'accepted':
        return jsonify({'status': 'connected'})
    elif conn.requester_id == current['id']:
        return jsonify({'status': 'pending_sent'})
    else:
        return jsonify({'status': 'pending_received', 'connection_id': conn.id})


@app.route('/api/social/suggest_skills')
@social_login_required
def api_suggest_skills():
    """API to get skill suggestions"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    # Get unique skill names that match
    skills = db.session.query(Skill.name).filter(
        Skill.name.ilike(f'%{query}%')
    ).distinct().limit(10).all()
    
    return jsonify([s[0] for s in skills])


@app.route('/api/social/suggest_hobbies')
@social_login_required
def api_suggest_hobbies():
    """API to get hobby suggestions"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify([])
    
    hobbies = db.session.query(Hobby.name).filter(
        Hobby.name.ilike(f'%{query}%')
    ).distinct().limit(10).all()
    
    return jsonify([h[0] for h in hobbies])


@app.route('/api/social/stats')
@social_login_required
def api_social_stats():
    """Get user's social stats"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    connections_count = Connection.query.filter(
        ((Connection.requester_id == current['id']) | (Connection.receiver_id == current['id'])) &
        (Connection.status == 'accepted')
    ).count()
    
    posts_count = Post.query.filter_by(author_id=current['id'], author_type=current['type']).count()
    
    # Total endorsements received
    total_endorsements = 0
    for skill in profile.skills:
        total_endorsements += len(skill.endorsements)
    
    return jsonify({
        'connections': connections_count,
        'achievements': len(profile.achievements),
        'skills': len(profile.skills),
        'experiences': len(profile.experiences),
        'hobbies': len(profile.hobbies),
        'posts': posts_count,
        'endorsements': total_endorsements
    })


# ==================== ADMIN - ALUMNI MANAGEMENT ====================

@app.route('/admin/alumni', methods=['GET'])
@admin_required
def list_alumni():
    """List all alumni"""
    alumni_list = Alumni.query.order_by(Alumni.graduation_year.desc()).all()
    return render_template('list_alumni.html', alumni_list=alumni_list)


@app.route('/admin/add_alumni', methods=['GET', 'POST'])
@admin_required
def add_alumni():
    """Add new alumni (admin only)"""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        graduation_year = int(request.form['graduation_year'])
        degree = request.form.get('degree', '')
        major = request.form.get('major', '')
        phone = request.form.get('phone', '')
        
        existing = Alumni.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'error')
            return redirect(url_for('add_alumni'))
        
        new_alumni = Alumni(
            name=name,
            email=email,
            graduation_year=graduation_year,
            degree=degree,
            major=major,
            phone=phone
        )
        new_alumni.set_password(password)
        db.session.add(new_alumni)
        db.session.commit()
        
        new_alumni.alumni_id = f'ALM_{new_alumni.id:03d}'
        db.session.commit()
        
        # Create profile
        get_user_profile(new_alumni.alumni_id, 'alumni')
        
        flash('Alumni added successfully!', 'success')
        return redirect(url_for('list_alumni'))
    
    return render_template('add_alumni.html')


# Add this to your logout route to handle alumni
@app.route('/logout_social')
def logout_social():
    user_type = session.get('user_type')
    session.clear()
    flash('You have been logged out', 'info')
    
    if user_type == 'admin':
        return redirect(url_for('admin_login'))
    elif user_type == 'teacher':
        return redirect(url_for('teacher_login'))
    elif user_type == 'alumni':
        return redirect(url_for('alumni_login'))
    else:
        return redirect(url_for('student_login'))
    
    # ==================== ACHIEVEMENT MANAGEMENT ====================

@app.route('/social/achievements/add', methods=['GET', 'POST'])
@social_login_required
def add_achievement():
    """Add new achievement"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        category = request.form['category']
        date_achieved = datetime.strptime(request.form['date_achieved'], '%Y-%m-%d').date()
        issuer = request.form.get('issuer', '')
        certificate_url = request.form.get('certificate_url', '')
        
        new_achievement = Achievement(
            profile_id=profile.id,
            title=title,
            description=description,
            category=category,
            date_achieved=date_achieved,
            issuer=issuer,
            certificate_url=certificate_url
        )
        
        db.session.add(new_achievement)
        db.session.commit()
        
        flash('Achievement added successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('add_achievement.html', current_user=current)


@app.route('/social/achievements/<int:achievement_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_achievement(achievement_id):
    """Edit achievement"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    achievement = Achievement.query.get_or_404(achievement_id)
    
    if achievement.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    if request.method == 'POST':
        achievement.title = request.form['title']
        achievement.description = request.form.get('description', '')
        achievement.category = request.form['category']
        achievement.date_achieved = datetime.strptime(request.form['date_achieved'], '%Y-%m-%d').date()
        achievement.issuer = request.form.get('issuer', '')
        achievement.certificate_url = request.form.get('certificate_url', '')
        
        db.session.commit()
        
        flash('Achievement updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_achievement.html', current_user=current, achievement=achievement)


@app.route('/social/achievements/<int:achievement_id>/delete', methods=['POST'])
@social_login_required
def delete_achievement(achievement_id):
    """Delete achievement"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    achievement = Achievement.query.get_or_404(achievement_id)
    
    if achievement.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    db.session.delete(achievement)
    db.session.commit()
    
    flash('Achievement deleted', 'success')
    return redirect(url_for('my_profile'))


# ==================== SKILL MANAGEMENT ====================

@app.route('/social/skills/add', methods=['GET', 'POST'])
@social_login_required
def add_skill():
    """Add new skill"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        name = request.form['name']
        proficiency = request.form['proficiency']
        category = request.form['category']
        
        # Check if skill already exists for this profile
        existing = Skill.query.filter_by(profile_id=profile.id, name=name).first()
        if existing:
            flash('This skill already exists in your profile', 'warning')
            return redirect(url_for('add_skill'))
        
        new_skill = Skill(
            profile_id=profile.id,
            name=name,
            proficiency=proficiency,
            category=category
        )
        
        db.session.add(new_skill)
        db.session.commit()
        
        flash('Skill added successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('add_skill.html', current_user=current)


@app.route('/social/skills/<int:skill_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_skill(skill_id):
    """Edit skill"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    skill = Skill.query.get_or_404(skill_id)
    
    if skill.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    if request.method == 'POST':
        skill.name = request.form['name']
        skill.proficiency = request.form['proficiency']
        skill.category = request.form['category']
        
        db.session.commit()
        
        flash('Skill updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_skill.html', current_user=current, skill=skill)


@app.route('/social/skills/<int:skill_id>/endorse', methods=['POST'])
@social_login_required
def endorse_skill(skill_id):
    """Endorse a skill"""
    current = get_current_user()
    skill = Skill.query.get_or_404(skill_id)
    
    # Check if already endorsed
    existing = SkillEndorsement.query.filter_by(skill_id=skill_id, endorser_id=current['id']).first()
    if existing:
        flash('You have already endorsed this skill', 'warning')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    # Can't endorse own skills
    if skill.profile.user_id == current['id']:
        flash('You cannot endorse your own skills', 'error')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    new_endorsement = SkillEndorsement(
        skill_id=skill_id,
        endorser_id=current['id'],
        endorser_type=current['type']
    )
    
    db.session.add(new_endorsement)
    db.session.commit()
    
    flash('Skill endorsed!', 'success')
    return redirect(request.referrer or url_for('social_dashboard'))


@app.route('/social/skills/<int:skill_id>/unendorse', methods=['POST'])
@social_login_required
def unendorse_skill(skill_id):
    """Remove skill endorsement"""
    current = get_current_user()
    
    endorsement = SkillEndorsement.query.filter_by(
        skill_id=skill_id, 
        endorser_id=current['id']
    ).first()
    
    if endorsement:
        db.session.delete(endorsement)
        db.session.commit()
        flash('Endorsement removed', 'info')
    
    return redirect(request.referrer or url_for('social_dashboard'))


@app.route('/social/skills/<int:skill_id>/delete', methods=['POST'])
@social_login_required
def delete_skill(skill_id):
    """Delete skill"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    skill = Skill.query.get_or_404(skill_id)
    
    if skill.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    db.session.delete(skill)
    db.session.commit()
    
    flash('Skill deleted', 'success')
    return redirect(url_for('my_profile'))


# ==================== EXPERIENCE MANAGEMENT ====================

@app.route('/social/experience/add', methods=['GET', 'POST'])
@social_login_required
def add_experience():
    """Add work experience"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form.get('location', '')
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        is_current = 'is_current' in request.form
        end_date = None if is_current else datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        description = request.form.get('description', '')
        
        new_experience = Experience(
            profile_id=profile.id,
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
            description=description
        )
        
        db.session.add(new_experience)
        db.session.commit()
        
        flash('Experience added successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('add_experience.html', current_user=current)


@app.route('/social/experience/<int:exp_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_experience(exp_id):
    """Edit experience"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    experience = Experience.query.get_or_404(exp_id)
    
    if experience.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    if request.method == 'POST':
        experience.title = request.form['title']
        experience.company = request.form['company']
        experience.location = request.form.get('location', '')
        experience.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        experience.is_current = 'is_current' in request.form
        experience.end_date = None if experience.is_current else datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        experience.description = request.form.get('description', '')
        
        db.session.commit()
        
        flash('Experience updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_experience.html', current_user=current, experience=experience)


@app.route('/social/experience/<int:exp_id>/delete', methods=['POST'])
@social_login_required
def delete_experience(exp_id):
    """Delete experience"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    experience = Experience.query.get_or_404(exp_id)
    
    if experience.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    db.session.delete(experience)
    db.session.commit()
    
    flash('Experience deleted', 'success')
    return redirect(url_for('my_profile'))


# ==================== HOBBY MANAGEMENT ====================

@app.route('/social/hobbies/add', methods=['GET', 'POST'])
@social_login_required
def add_hobby():
    """Add hobby"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        category = request.form['category']
        
        new_hobby = Hobby(
            profile_id=profile.id,
            name=name,
            description=description,
            category=category
        )
        
        db.session.add(new_hobby)
        db.session.commit()
        
        flash('Hobby added successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('add_hobby.html', current_user=current)


@app.route('/social/hobbies/<int:hobby_id>/edit', methods=['GET', 'POST'])
@social_login_required
def edit_hobby(hobby_id):
    """Edit hobby"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    hobby = Hobby.query.get_or_404(hobby_id)
    
    if hobby.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    if request.method == 'POST':
        hobby.name = request.form['name']
        hobby.description = request.form.get('description', '')
        hobby.category = request.form['category']
        
        db.session.commit()
        
        flash('Hobby updated successfully!', 'success')
        return redirect(url_for('my_profile'))
    
    return render_template('edit_hobby.html', current_user=current, hobby=hobby)


@app.route('/social/hobbies/<int:hobby_id>/delete', methods=['POST'])
@social_login_required
def delete_hobby(hobby_id):
    """Delete hobby"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    hobby = Hobby.query.get_or_404(hobby_id)
    
    if hobby.profile_id != profile.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_profile'))
    
    db.session.delete(hobby)
    db.session.commit()
    
    flash('Hobby deleted', 'success')
    return redirect(url_for('my_profile'))


# ==================== CONNECTION MANAGEMENT ====================

@app.route('/social/connect/<user_type>/<user_id>', methods=['POST'])
@social_login_required
def send_connection_request(user_type, user_id):
    """Send connection request"""
    current = get_current_user()
    
    # Can't connect to self
    if current['id'] == user_id and current['type'] == user_type:
        flash('You cannot connect with yourself', 'error')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    # Check if connection already exists
    existing = Connection.query.filter(
        ((Connection.requester_id == current['id']) & (Connection.receiver_id == user_id)) |
        ((Connection.requester_id == user_id) & (Connection.receiver_id == current['id']))
    ).first()
    
    if existing:
        flash('Connection request already exists', 'warning')
        return redirect(request.referrer or url_for('social_dashboard'))
    
    message = request.form.get('message', '')
    
    new_connection = Connection(
        requester_id=current['id'],
        requester_type=current['type'],
        receiver_id=user_id,
        receiver_type=user_type,
        message=message
    )
    
    db.session.add(new_connection)
    db.session.commit()
    
    flash('Connection request sent!', 'success')
    return redirect(request.referrer or url_for('social_dashboard'))


@app.route('/social/connections')
@social_login_required
def my_connections():
    """View all connections"""
    current = get_current_user()
    
    # Get accepted connections
    connections = Connection.query.filter(
        ((Connection.requester_id == current['id']) | (Connection.receiver_id == current['id'])) &
        (Connection.status == 'accepted')
    ).all()
    
    connection_list = []
    for conn in connections:
        if conn.requester_id == current['id']:
            other_id = conn.receiver_id
            other_type = conn.receiver_type
        else:
            other_id = conn.requester_id
            other_type = conn.requester_type
        
        user_info = get_user_info(other_id, other_type)
        profile = get_user_profile(other_id, other_type)
        connection_list.append({
            'user': user_info,
            'type': other_type,
            'profile': profile,
            'connected_at': conn.responded_at or conn.requested_at,
            'connection_id': conn.id
        })
    
    # Get pending requests (received)
    pending_requests = Connection.query.filter_by(
        receiver_id=current['id'],
        status='pending'
    ).all()
    
    pending_list = []
    for req in pending_requests:
        user_info = get_user_info(req.requester_id, req.requester_type)
        profile = get_user_profile(req.requester_id, req.requester_type)
        pending_list.append({
            'request': req,
            'user': user_info,
            'type': req.requester_type,
            'profile': profile
        })
    
    # Get sent requests
    sent_requests = Connection.query.filter_by(
        requester_id=current['id'],
        status='pending'
    ).all()
    
    sent_list = []
    for req in sent_requests:
        user_info = get_user_info(req.receiver_id, req.receiver_type)
        sent_list.append({
            'request': req,
            'user': user_info,
            'type': req.receiver_type
        })
    
    return render_template('my_connections.html',
                         current_user=current,
                         connections=connection_list,
                         pending_requests=pending_list,
                         sent_requests=sent_list)


@app.route('/social/connection/<int:connection_id>/accept', methods=['POST'])
@social_login_required
def accept_connection(connection_id):
    """Accept connection request"""
    current = get_current_user()
    connection = Connection.query.get_or_404(connection_id)
    
    if connection.receiver_id != current['id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_connections'))
    
    connection.status = 'accepted'
    connection.responded_at = datetime.now(timezone.utc)
    db.session.commit()
    
    flash('Connection accepted!', 'success')
    return redirect(url_for('my_connections'))


@app.route('/social/connection/<int:connection_id>/reject', methods=['POST'])
@social_login_required
def reject_connection(connection_id):
    """Reject connection request"""
    current = get_current_user()
    connection = Connection.query.get_or_404(connection_id)
    
    if connection.receiver_id != current['id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_connections'))
    
    connection.status = 'rejected'
    connection.responded_at = datetime.now(timezone.utc)
    db.session.commit()
    
    flash('Connection rejected', 'info')
    return redirect(url_for('my_connections'))


@app.route('/social/connection/<int:connection_id>/cancel', methods=['POST'])
@social_login_required
def cancel_connection_request(connection_id):
    """Cancel sent connection request"""
    current = get_current_user()
    connection = Connection.query.get_or_404(connection_id)
    
    if connection.requester_id != current['id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_connections'))
    
    db.session.delete(connection)
    db.session.commit()
    
    flash('Connection request cancelled', 'info')
    return redirect(url_for('my_connections'))


@app.route('/social/connection/<int:connection_id>/remove', methods=['POST'])
@social_login_required
def remove_connection(connection_id):
    """Remove existing connection"""
    current = get_current_user()
    connection = Connection.query.get_or_404(connection_id)
    
    if connection.requester_id != current['id'] and connection.receiver_id != current['id']:
        flash('Unauthorized', 'error')
        return redirect(url_for('my_connections'))
    
    db.session.delete(connection)
    db.session.commit()
    
    flash('Connection removed', 'info')
    return redirect(url_for('my_connections'))


# ==================== SEARCH & DISCOVERY ====================

@app.route('/social/search')
@social_login_required
def search_people():
    """Search for people"""
    current = get_current_user()
    
    query = request.args.get('q', '')
    filter_type = request.args.get('type', 'all')  # all, students, teachers, alumni
    filter_skill = request.args.get('skill', '')
    filter_hobby = request.args.get('hobby', '')
    filter_achievement = request.args.get('achievement', '')
    
    results = []
    
    if query or filter_skill or filter_hobby or filter_achievement:
        # Search students
        if filter_type in ['all', 'students']:
            students = Student.query.filter(
                (Student.name.ilike(f'%{query}%')) | (Student.email.ilike(f'%{query}%'))
            ).all()
            
            for student in students:
                profile = get_user_profile(student.student_id, 'student')
                
                # Apply filters
                if filter_skill:
                    if not any(s.name.lower() == filter_skill.lower() for s in profile.skills):
                        continue
                if filter_hobby:
                    if not any(h.name.lower() == filter_hobby.lower() for h in profile.hobbies):
                        continue
                if filter_achievement:
                    if not any(filter_achievement.lower() in a.title.lower() for a in profile.achievements):
                        continue
                
                results.append({
                    'user': {'name': student.name, 'email': student.email, 'id': student.student_id},
                    'type': 'student',
                    'profile': profile
                })
        
        # Search teachers
        if filter_type in ['all', 'teachers']:
            teachers = Teacher.query.filter(
                (Teacher.name.ilike(f'%{query}%')) | (Teacher.email.ilike(f'%{query}%'))
            ).all()
            
            for teacher in teachers:
                profile = get_user_profile(teacher.teacher_id, 'teacher')
                
                if filter_skill:
                    if not any(s.name.lower() == filter_skill.lower() for s in profile.skills):
                        continue
                if filter_hobby:
                    if not any(h.name.lower() == filter_hobby.lower() for h in profile.hobbies):
                        continue
                if filter_achievement:
                    if not any(filter_achievement.lower() in a.title.lower() for a in profile.achievements):
                        continue
                
                results.append({
                    'user': {'name': teacher.name, 'email': teacher.email, 'id': teacher.teacher_id},
                    'type': 'teacher',
                    'profile': profile
                })
        
        # Search alumni
        if filter_type in ['all', 'alumni']:
            alumni_list = Alumni.query.filter(
                (Alumni.name.ilike(f'%{query}%')) | (Alumni.email.ilike(f'%{query}%'))
            ).all()
            
            for alumni in alumni_list:
                profile = get_user_profile(alumni.alumni_id, 'alumni')
                
                if filter_skill:
                    if not any(s.name.lower() == filter_skill.lower() for s in profile.skills):
                        continue
                if filter_hobby:
                    if not any(h.name.lower() == filter_hobby.lower() for h in profile.hobbies):
                        continue
                if filter_achievement:
                    if not any(filter_achievement.lower() in a.title.lower() for a in profile.achievements):
                        continue
                
                results.append({
                    'user': {'name': alumni.name, 'email': alumni.email, 'id': alumni.alumni_id},
                    'type': 'alumni',
                    'profile': profile
                })
    
    # Add connection status to results
    for result in results:
        result['connection_status'] = None
        if result['user']['id'] != current['id']:
            conn = Connection.query.filter(
                ((Connection.requester_id == current['id']) & (Connection.receiver_id == result['user']['id'])) |
                ((Connection.requester_id == result['user']['id']) & (Connection.receiver_id == current['id']))
            ).first()
            
            if conn:
                if conn.status == 'accepted':
                    result['connection_status'] = 'connected'
                elif conn.requester_id == current['id']:
                    result['connection_status'] = 'pending_sent'
                else:
                    result['connection_status'] = 'pending_received'
    
    return render_template('search_people.html',
                         current_user=current,
                         results=results,
                         query=query,
                         filter_type=filter_type,
                         filter_skill=filter_skill,
                         filter_hobby=filter_hobby,
                         filter_achievement=filter_achievement)


@app.route('/social/discover')
@social_login_required
def discover():
    """Discover new people to connect with"""
    current = get_current_user()
    profile = get_user_profile(current['id'], current['type'])
    
    # Get users with similar skills
    my_skills = [s.name.lower() for s in profile.skills]
    
    suggestions = []
    
    # Get all profiles with skills
    all_profiles = UserProfile.query.filter(
        UserProfile.user_id != current['id']
    ).limit(50).all()
    
    for p in all_profiles:
        # Skip if already connected
        if are_connected(current['id'], p.user_id):
            continue
        
        # Check for pending connection
        conn = Connection.query.filter(
            ((Connection.requester_id == current['id']) & (Connection.receiver_id == p.user_id)) |
            ((Connection.requester_id == p.user_id) & (Connection.receiver_id == current['id']))
        ).first()
        
        if conn:
            continue
        
        # Calculate match score
        their_skills = [s.name.lower() for s in p.skills]
        common_skills = set(my_skills) & set(their_skills)
        
        if len(common_skills) > 0 or len(suggestions) < 20:
            user_info = get_user_info(p.user_id, p.user_type)
            if user_info:
                suggestions.append({
                    'user': user_info,
                    'type': p.user_type,
                    'profile': p,
                    'common_skills': list(common_skills),
                    'match_score': len(common_skills)
                })
    
    # Sort by match score
    suggestions.sort(key=lambda x: x['match_score'], reverse=True)
    
    return render_template('discover.html',
                         current_user=current,
                         suggestions=suggestions[:20])


# ==================== ALUMNI DIRECTORY ====================

@app.route('/social/alumni')
@social_login_required
def alumni_directory():
    """Browse alumni directory"""
    current = get_current_user()
    
    # Filters
    graduation_year = request.args.get('year', type=int)
    company = request.args.get('company', '')
    
    query = Alumni.query
    
    if graduation_year:
        query = query.filter_by(graduation_year=graduation_year)
    if company:
        query = query.filter(Alumni.current_company.ilike(f'%{company}%'))
    
    alumni_list = query.order_by(Alumni.graduation_year.desc()).all()
    
    # Get unique graduation years for filter
    years = db.session.query(Alumni.graduation_year).distinct().order_by(Alumni.graduation_year.desc()).all()
    years = [y[0] for y in years]
    
    # Add profile and connection info
    alumni_data = []
    for alumni in alumni_list:
        profile = get_user_profile(alumni.alumni_id, 'alumni')
        
        # Check connection status
        connection_status = None
        if alumni.alumni_id != current['id']:
            conn = Connection.query.filter(
                ((Connection.requester_id == current['id']) & (Connection.receiver_id == alumni.alumni_id)) |
                ((Connection.requester_id == alumni.alumni_id) & (Connection.receiver_id == current['id']))
            ).first()
            
            if conn:
                if conn.status == 'accepted':
                    connection_status = 'connected'
                elif conn.requester_id == current['id']:
                    connection_status = 'pending_sent'
                else:
                    connection_status = 'pending_received'
        
        alumni_data.append({
            'alumni': alumni,
            'profile': profile,
            'connection_status': connection_status
        })
    
    return render_template('alumni_directory.html',
                         current_user=current,
                         alumni_list=alumni_data,
                         years=years,
                         selected_year=graduation_year,
                         company_filter=company)