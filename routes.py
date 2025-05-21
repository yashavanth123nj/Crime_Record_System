from flask import render_template, redirect, url_for, flash, request, jsonify, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from sqlalchemy import func, extract, desc, or_
from datetime import datetime, date, timedelta
import calendar

from app import app, db
from models import (User, Crime, Criminal, CriminalCrime, Case, CaseNote, 
                   Victim, Witness, Evidence, PoliceStation, PoliceOfficer)
from forms import (LoginForm, RegistrationForm, EditProfileForm, ChangePasswordForm,
                  CrimeForm, CrimeSearchForm, CriminalForm, CriminalSearchForm,
                  CaseForm, CaseNoteForm, CaseSearchForm, VictimForm, WitnessForm,
                  EvidenceForm, PoliceStationForm, PoliceOfficerForm)
from utils import role_required

# Home and authentication routes
@app.route('/')
def index():
    return render_template('dashboard.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        
        if not user.is_active:
            flash('Your account is inactive. Please contact an administrator.', 'warning')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('index')
        
        flash('Login successful!', 'success')
        return redirect(next_page)
    
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User registration successful!', 'success')
        return redirect(url_for('user_list'))
    
    return render_template('user/add.html', title='Register User', form=form)

# User management routes
@app.route('/users')
@login_required
@role_required('admin')
def user_list():
    users = User.query.all()
    return render_template('user/list.html', title='User Management', users=users)

@app.route('/users/<int:id>')
@login_required
def user_profile(id):
    user = User.query.get_or_404(id)
    if current_user.id != user.id and not current_user.is_admin():
        abort(403)
    
    return render_template('user/profile.html', title='User Profile', user=user)

@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(id):
    user = User.query.get_or_404(id)
    if current_user.id != user.id and not current_user.is_admin():
        abort(403)
    
    form = EditProfileForm(user.username, user.email)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_profile', id=user.id))
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
    
    return render_template('user/add.html', title='Edit Profile', form=form)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('change_password'))
        
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been changed successfully!', 'success')
        return redirect(url_for('user_profile', id=current_user.id))
    
    return render_template('user/change_password.html', title='Change Password', form=form)

# Dashboard and analytics
@app.route('/dashboard')
@login_required
def dashboard():
    # Get crime statistics for the dashboard
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    start_of_year = date(today.year, 1, 1)
    
    total_crimes = Crime.query.count()
    active_cases = Case.query.filter(Case.status != 'closed').count()
    crimes_this_month = Crime.query.filter(Crime.date >= start_of_month).count()
    crimes_this_year = Crime.query.filter(Crime.date >= start_of_year).count()
    
    # Recent crimes
    recent_crimes = Crime.query.order_by(Crime.date.desc()).limit(5).all()
    
    # Crime types distribution
    crime_types = db.session.query(
        Crime.type, func.count(Crime.id).label('count')
    ).group_by(Crime.type).order_by(desc('count')).limit(5).all()
    
    # Monthly crime trend
    current_year = today.year
    monthly_crimes = db.session.query(
        extract('month', Crime.date).label('month'),
        func.count(Crime.id).label('count')
    ).filter(extract('year', Crime.date) == current_year).group_by('month').all()
    
    # Format data for charts
    months = []
    counts = []
    for i in range(1, 13):
        month_name = calendar.month_abbr[i]
        months.append(month_name)
        
        # Find the count for this month
        count = 0
        for m in monthly_crimes:
            if int(m.month) == i:
                count = m.count
                break
        
        counts.append(count)
    
    # Crime type labels and data for pie chart
    type_labels = [t.type for t in crime_types]
    type_data = [t.count for t in crime_types]
    
    # Get high-priority cases
    high_priority_cases = Case.query.filter_by(priority='high').order_by(Case.updated_at.desc()).limit(3).all()
    
    return render_template('dashboard.html', 
                           title='Dashboard',
                           total_crimes=total_crimes,
                           active_cases=active_cases,
                           crimes_this_month=crimes_this_month,
                           crimes_this_year=crimes_this_year,
                           recent_crimes=recent_crimes,
                           high_priority_cases=high_priority_cases,
                           months=months,
                           counts=counts,
                           type_labels=type_labels,
                           type_data=type_data)

# Crime routes
@app.route('/crimes')
@login_required
def crime_list():
    form = CrimeSearchForm()
    
    page = request.args.get('page', 1, type=int)
    query = Crime.query
    
    # Apply filters if provided
    if request.args.get('search_term'):
        search = "%{}%".format(request.args.get('search_term'))
        query = query.filter(or_(
            Crime.type.like(search),
            Crime.description.like(search),
            Crime.location.like(search)
        ))
    
    if request.args.get('crime_type'):
        query = query.filter(Crime.type == request.args.get('crime_type'))
    
    if request.args.get('date_from'):
        date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d').date()
        query = query.filter(Crime.date >= date_from)
    
    if request.args.get('date_to'):
        date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d').date()
        query = query.filter(Crime.date <= date_to)
    
    if request.args.get('location'):
        location = "%{}%".format(request.args.get('location'))
        query = query.filter(Crime.location.like(location))
    
    if request.args.get('status') and request.args.get('status') != '':
        query = query.filter(Crime.status == request.args.get('status'))
    
    # Get unique crime types for filter dropdown
    crime_types = db.session.query(Crime.type).distinct().all()
    crime_types = [t[0] for t in crime_types]
    
    crimes = query.order_by(Crime.date.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('crime/list.html', 
                           title='Crime Records',
                           crimes=crimes,
                           form=form,
                           crime_types=crime_types)

@app.route('/crimes/add', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def add_crime():
    form = CrimeForm()
    
    if form.validate_on_submit():
        crime = Crime(
            type=form.type.data,
            description=form.description.data,
            date=form.date.data,
            time=form.time.data,
            location=form.location.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            status=form.status.data
        )
        
        db.session.add(crime)
        db.session.commit()
        flash('Crime record added successfully!', 'success')
        return redirect(url_for('crime_list'))
    
    return render_template('crime/add.html', title='Add Crime Record', form=form)

@app.route('/crimes/<int:id>')
@login_required
def view_crime(id):
    crime = Crime.query.get_or_404(id)
    
    # Get related criminals, victims, witnesses, cases, and evidence
    criminals = db.session.query(Criminal).join(CriminalCrime).filter(CriminalCrime.crime_id == id).all()
    victims = Victim.query.filter_by(crime_id=id).all()
    witnesses = Witness.query.filter_by(crime_id=id).all()
    cases = Case.query.filter_by(crime_id=id).all()
    evidence = Evidence.query.filter_by(crime_id=id).all()
    
    return render_template('crime/view.html',
                          title=f'Crime #{id}',
                          crime=crime,
                          criminals=criminals,
                          victims=victims,
                          witnesses=witnesses,
                          cases=cases,
                          evidence=evidence)

@app.route('/crimes/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def edit_crime(id):
    crime = Crime.query.get_or_404(id)
    form = CrimeForm()
    
    if form.validate_on_submit():
        crime.type = form.type.data
        crime.description = form.description.data
        crime.date = form.date.data
        crime.time = form.time.data
        crime.location = form.location.data
        crime.latitude = form.latitude.data
        crime.longitude = form.longitude.data
        crime.status = form.status.data
        
        db.session.commit()
        flash('Crime record updated successfully!', 'success')
        return redirect(url_for('view_crime', id=crime.id))
    
    elif request.method == 'GET':
        form.type.data = crime.type
        form.description.data = crime.description
        form.date.data = crime.date
        form.time.data = crime.time
        form.location.data = crime.location
        form.latitude.data = crime.latitude
        form.longitude.data = crime.longitude
        form.status.data = crime.status
    
    return render_template('crime/add.html', title='Edit Crime Record', form=form)

# Criminal routes
@app.route('/criminals')
@login_required
def criminal_list():
    form = CriminalSearchForm()
    
    page = request.args.get('page', 1, type=int)
    query = Criminal.query
    
    # Apply filters if provided
    if request.args.get('search_term'):
        search = "%{}%".format(request.args.get('search_term'))
        query = query.filter(or_(
            Criminal.name.like(search),
            Criminal.alias.like(search),
            Criminal.address.like(search),
            Criminal.nationality.like(search)
        ))
    
    if request.args.get('gender') and request.args.get('gender') != '':
        query = query.filter(Criminal.gender == request.args.get('gender'))
    
    if request.args.get('nationality'):
        nationality = "%{}%".format(request.args.get('nationality'))
        query = query.filter(Criminal.nationality.like(nationality))
    
    criminals = query.order_by(Criminal.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('criminal/list.html',
                          title='Criminal Records',
                          criminals=criminals,
                          form=form)

@app.route('/criminals/add', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def add_criminal():
    form = CriminalForm()
    
    if form.validate_on_submit():
        criminal = Criminal(
            name=form.name.data,
            alias=form.alias.data,
            gender=form.gender.data,
            date_of_birth=form.date_of_birth.data,
            address=form.address.data,
            nationality=form.nationality.data,
            identification_marks=form.identification_marks.data,
            photo_url=form.photo_url.data
        )
        
        db.session.add(criminal)
        db.session.commit()
        flash('Criminal record added successfully!', 'success')
        return redirect(url_for('criminal_list'))
    
    return render_template('criminal/add.html', title='Add Criminal Record', form=form)

@app.route('/criminals/<int:id>')
@login_required
def view_criminal(id):
    criminal = Criminal.query.get_or_404(id)
    
    # Get related crimes
    crimes = db.session.query(Crime).join(CriminalCrime).filter(CriminalCrime.criminal_id == id).all()
    
    return render_template('criminal/view.html',
                          title=f'Criminal - {criminal.name}',
                          criminal=criminal,
                          crimes=crimes)

@app.route('/criminals/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def edit_criminal(id):
    criminal = Criminal.query.get_or_404(id)
    form = CriminalForm()
    
    if form.validate_on_submit():
        criminal.name = form.name.data
        criminal.alias = form.alias.data
        criminal.gender = form.gender.data
        criminal.date_of_birth = form.date_of_birth.data
        criminal.address = form.address.data
        criminal.nationality = form.nationality.data
        criminal.identification_marks = form.identification_marks.data
        criminal.photo_url = form.photo_url.data
        
        db.session.commit()
        flash('Criminal record updated successfully!', 'success')
        return redirect(url_for('view_criminal', id=criminal.id))
    
    elif request.method == 'GET':
        form.name.data = criminal.name
        form.alias.data = criminal.alias
        form.gender.data = criminal.gender
        form.date_of_birth.data = criminal.date_of_birth
        form.address.data = criminal.address
        form.nationality.data = criminal.nationality
        form.identification_marks.data = criminal.identification_marks
        form.photo_url.data = criminal.photo_url
    
    return render_template('criminal/add.html', title='Edit Criminal Record', form=form)

@app.route('/criminals/<int:criminal_id>/add_crime/<int:crime_id>', methods=['POST'])
@login_required
@role_required('officer')
def link_criminal_to_crime(criminal_id, crime_id):
    criminal = Criminal.query.get_or_404(criminal_id)
    crime = Crime.query.get_or_404(crime_id)
    
    # Check if the relationship already exists
    existing = CriminalCrime.query.filter_by(
        criminal_id=criminal_id, crime_id=crime_id).first()
    
    if not existing:
        role = request.form.get('role', 'suspect')
        criminal_crime = CriminalCrime(
            criminal_id=criminal_id,
            crime_id=crime_id,
            role=role
        )
        db.session.add(criminal_crime)
        db.session.commit()
        flash(f'Criminal {criminal.name} linked to Crime #{crime.id} successfully!', 'success')
    else:
        flash('Criminal is already linked to this crime.', 'warning')
    
    return redirect(url_for('view_crime', id=crime_id))

# Case management routes
@app.route('/cases')
@login_required
def case_list():
    form = CaseSearchForm()
    
    # Populate officer dropdown
    officers = User.query.filter(User.role.in_(['admin', 'officer'])).all()
    form.officer_id.choices = [(0, 'All Officers')] + [(o.id, f"{o.first_name} {o.last_name}") for o in officers]
    
    page = request.args.get('page', 1, type=int)
    query = Case.query
    
    # Apply filters if provided
    if request.args.get('search_term'):
        search = "%{}%".format(request.args.get('search_term'))
        query = query.filter(or_(
            Case.title.like(search),
            Case.description.like(search)
        ))
    
    if request.args.get('status') and request.args.get('status') != '':
        query = query.filter(Case.status == request.args.get('status'))
    
    if request.args.get('priority') and request.args.get('priority') != '':
        query = query.filter(Case.priority == request.args.get('priority'))
    
    if request.args.get('officer_id') and request.args.get('officer_id') != '0':
        officer_id = int(request.args.get('officer_id'))
        query = query.filter(Case.officer_id == officer_id)
    
    # Add additional restrictions based on user role
    if not current_user.is_admin():
        query = query.filter(Case.officer_id == current_user.id)
    
    cases = query.order_by(Case.updated_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('case/list.html',
                          title='Case Management',
                          cases=cases,
                          form=form)

@app.route('/cases/add', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def add_case():
    form = CaseForm()
    
    # Populate dropdown options
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"{c.type} - {c.date} at {c.location}") for c in crimes]
    
    officers = User.query.filter(User.role.in_(['admin', 'officer'])).all()
    form.officer_id.choices = [(o.id, f"{o.first_name} {o.last_name}") for o in officers]
    
    if form.validate_on_submit():
        case = Case(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            crime_id=form.crime_id.data,
            officer_id=form.officer_id.data
        )
        
        db.session.add(case)
        db.session.commit()
        flash('Case created successfully!', 'success')
        return redirect(url_for('case_list'))
    
    return render_template('case/add.html', title='Create New Case', form=form)

@app.route('/cases/<int:id>')
@login_required
def view_case(id):
    case = Case.query.get_or_404(id)
    
    # Check permission
    if not current_user.is_admin() and case.officer_id != current_user.id:
        abort(403)
    
    # Get related crime
    crime = Crime.query.get(case.crime_id) if case.crime_id else None
    
    # Get assigned officer
    officer = User.query.get(case.officer_id) if case.officer_id else None
    
    # Get case notes
    notes = CaseNote.query.filter_by(case_id=id).order_by(CaseNote.created_at.desc()).all()
    
    # Note form
    note_form = CaseNoteForm()
    
    return render_template('case/view.html',
                          title=f'Case - {case.title}',
                          case=case,
                          crime=crime,
                          officer=officer,
                          notes=notes,
                          note_form=note_form)

@app.route('/cases/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def edit_case(id):
    case = Case.query.get_or_404(id)
    
    # Check permission
    if not current_user.is_admin() and case.officer_id != current_user.id:
        abort(403)
    
    form = CaseForm()
    
    # Populate dropdown options
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"{c.type} - {c.date} at {c.location}") for c in crimes]
    
    officers = User.query.filter(User.role.in_(['admin', 'officer'])).all()
    form.officer_id.choices = [(o.id, f"{o.first_name} {o.last_name}") for o in officers]
    
    if form.validate_on_submit():
        case.title = form.title.data
        case.description = form.description.data
        case.status = form.status.data
        case.priority = form.priority.data
        case.crime_id = form.crime_id.data
        case.officer_id = form.officer_id.data
        
        db.session.commit()
        flash('Case updated successfully!', 'success')
        return redirect(url_for('view_case', id=case.id))
    
    elif request.method == 'GET':
        form.title.data = case.title
        form.description.data = case.description
        form.status.data = case.status
        form.priority.data = case.priority
        form.crime_id.data = case.crime_id
        form.officer_id.data = case.officer_id
    
    return render_template('case/add.html', title='Edit Case', form=form)

@app.route('/cases/<int:id>/add_note', methods=['POST'])
@login_required
def add_case_note(id):
    case = Case.query.get_or_404(id)
    
    # Check permission
    if not current_user.is_admin() and case.officer_id != current_user.id:
        abort(403)
    
    form = CaseNoteForm()
    
    if form.validate_on_submit():
        note = CaseNote(
            case_id=id,
            user_id=current_user.id,
            content=form.content.data
        )
        
        db.session.add(note)
        db.session.commit()
        flash('Note added successfully!', 'success')
    
    return redirect(url_for('view_case', id=id))

# Victim routes
@app.route('/victims')
@login_required
def victim_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Victim.query
    
    if search:
        search = f"%{search}%"
        query = query.filter(or_(
            Victim.name.like(search),
            Victim.contact.like(search),
            Victim.address.like(search)
        ))
    
    victims = query.order_by(Victim.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('victim/list.html',
                          title='Victim Records',
                          victims=victims,
                          search=search)

@app.route('/victims/add', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def add_victim():
    form = VictimForm()
    
    # Populate crime dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"{c.type} - {c.date} at {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        victim = Victim(
            name=form.name.data,
            gender=form.gender.data,
            age=form.age.data,
            contact=form.contact.data,
            address=form.address.data,
            statement=form.statement.data,
            crime_id=form.crime_id.data
        )
        
        db.session.add(victim)
        db.session.commit()
        flash('Victim record added successfully!', 'success')
        return redirect(url_for('victim_list'))
    
    return render_template('victim/add.html', title='Add Victim Record', form=form)

@app.route('/victims/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def edit_victim(id):
    victim = Victim.query.get_or_404(id)
    form = VictimForm()
    
    # Populate crime dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"{c.type} - {c.date} at {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        victim.name = form.name.data
        victim.gender = form.gender.data
        victim.age = form.age.data
        victim.contact = form.contact.data
        victim.address = form.address.data
        victim.statement = form.statement.data
        victim.crime_id = form.crime_id.data
        
        db.session.commit()
        flash('Victim record updated successfully!', 'success')
        return redirect(url_for('victim_list'))
    
    elif request.method == 'GET':
        form.name.data = victim.name
        form.gender.data = victim.gender
        form.age.data = victim.age
        form.contact.data = victim.contact
        form.address.data = victim.address
        form.statement.data = victim.statement
        form.crime_id.data = victim.crime_id
    
    return render_template('victim/add.html', title='Edit Victim Record', form=form)

# Witness routes
@app.route('/witnesses')
@login_required
def witness_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Witness.query
    
    if search:
        search = f"%{search}%"
        query = query.filter(or_(
            Witness.name.like(search),
            Witness.contact.like(search),
            Witness.address.like(search)
        ))
    
    witnesses = query.order_by(Witness.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('witness/list.html',
                          title='Witness Records',
                          witnesses=witnesses,
                          search=search)

@app.route('/witnesses/add', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def add_witness():
    form = WitnessForm()
    
    # Populate crime dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"{c.type} - {c.date} at {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        witness = Witness(
            name=form.name.data,
            contact=form.contact.data,
            address=form.address.data,
            statement=form.statement.data,
            relation_to_victim=form.relation_to_victim.data,
            crime_id=form.crime_id.data
        )
        
        db.session.add(witness)
        db.session.commit()
        flash('Witness record added successfully!', 'success')
        return redirect(url_for('witness_list'))
    
    return render_template('witness/add.html', title='Add Witness Record', form=form)

@app.route('/witnesses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def edit_witness(id):
    witness = Witness.query.get_or_404(id)
    form = WitnessForm()
    
    # Populate crime dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"{c.type} - {c.date} at {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        witness.name = form.name.data
        witness.contact = form.contact.data
        witness.address = form.address.data
        witness.statement = form.statement.data
        witness.relation_to_victim = form.relation_to_victim.data
        witness.crime_id = form.crime_id.data
        
        db.session.commit()
        flash('Witness record updated successfully!', 'success')
        return redirect(url_for('witness_list'))
    
    elif request.method == 'GET':
        form.name.data = witness.name
        form.contact.data = witness.contact
        form.address.data = witness.address
        form.statement.data = witness.statement
        form.relation_to_victim.data = witness.relation_to_victim
        form.crime_id.data = witness.crime_id
    
    return render_template('witness/add.html', title='Edit Witness Record', form=form)

# Evidence routes
@app.route('/evidence')
@login_required
def evidence_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Evidence.query
    
    if search:
        search = f"%{search}%"
        query = query.filter(or_(
            Evidence.name.like(search),
            Evidence.type.like(search),
            Evidence.description.like(search),
            Evidence.location_found.like(search),
            Evidence.custodian.like(search),
            Evidence.storage_location.like(search)
        ))
    
    evidence_items = query.order_by(Evidence.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('evidence/list.html',
                          title='Evidence Records',
                          evidence_items=evidence_items,
                          search=search)

@app.route('/evidence/add', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def add_evidence():
    form = EvidenceForm()
    
    # Populate crime dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"{c.type} - {c.date} at {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        evidence = Evidence(
            name=form.name.data,
            type=form.type.data,
            description=form.description.data,
            location_found=form.location_found.data,
            collection_date=form.collection_date.data,
            custodian=form.custodian.data,
            storage_location=form.storage_location.data,
            crime_id=form.crime_id.data
        )
        
        db.session.add(evidence)
        db.session.commit()
        flash('Evidence record added successfully!', 'success')
        return redirect(url_for('evidence_list'))
    
    return render_template('evidence/add.html', title='Add Evidence Record', form=form)

@app.route('/evidence/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('officer')
def edit_evidence(id):
    evidence = Evidence.query.get_or_404(id)
    form = EvidenceForm()
    
    # Populate crime dropdown
    crimes = Crime.query.all()
    form.crime_id.choices = [(c.id, f"{c.type} - {c.date} at {c.location}") for c in crimes]
    
    if form.validate_on_submit():
        evidence.name = form.name.data
        evidence.type = form.type.data
        evidence.description = form.description.data
        evidence.location_found = form.location_found.data
        evidence.collection_date = form.collection_date.data
        evidence.custodian = form.custodian.data
        evidence.storage_location = form.storage_location.data
        evidence.crime_id = form.crime_id.data
        
        db.session.commit()
        flash('Evidence record updated successfully!', 'success')
        return redirect(url_for('evidence_list'))
    
    elif request.method == 'GET':
        form.name.data = evidence.name
        form.type.data = evidence.type
        form.description.data = evidence.description
        form.location_found.data = evidence.location_found
        form.collection_date.data = evidence.collection_date
        form.custodian.data = evidence.custodian
        form.storage_location.data = evidence.storage_location
        form.crime_id.data = evidence.crime_id
    
    return render_template('evidence/add.html', title='Edit Evidence Record', form=form)

# Police Station routes
@app.route('/police_stations')
@login_required
def station_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = PoliceStation.query
    
    if search:
        search = f"%{search}%"
        query = query.filter(or_(
            PoliceStation.name.like(search),
            PoliceStation.address.like(search),
            PoliceStation.contact.like(search)
        ))
    
    stations = query.order_by(PoliceStation.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('police/stations.html',
                          title='Police Stations',
                          stations=stations,
                          search=search)

@app.route('/police_stations/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_station():
    form = PoliceStationForm()
    
    if form.validate_on_submit():
        station = PoliceStation(
            name=form.name.data,
            address=form.address.data,
            contact=form.contact.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data
        )
        
        db.session.add(station)
        db.session.commit()
        flash('Police station added successfully!', 'success')
        return redirect(url_for('station_list'))
    
    return render_template('police/add_station.html', title='Add Police Station', form=form)

@app.route('/police_stations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_station(id):
    station = PoliceStation.query.get_or_404(id)
    form = PoliceStationForm()
    
    if form.validate_on_submit():
        station.name = form.name.data
        station.address = form.address.data
        station.contact = form.contact.data
        station.latitude = form.latitude.data
        station.longitude = form.longitude.data
        
        db.session.commit()
        flash('Police station updated successfully!', 'success')
        return redirect(url_for('station_list'))
    
    elif request.method == 'GET':
        form.name.data = station.name
        form.address.data = station.address
        form.contact.data = station.contact
        form.latitude.data = station.latitude
        form.longitude.data = station.longitude
    
    return render_template('police/add_station.html', title='Edit Police Station', form=form)

# Police Officer routes
@app.route('/police_officers')
@login_required
def officer_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = PoliceOfficer.query
    
    if search:
        search = f"%{search}%"
        query = query.filter(or_(
            PoliceOfficer.name.like(search),
            PoliceOfficer.rank.like(search),
            PoliceOfficer.badge_number.like(search),
            PoliceOfficer.contact.like(search)
        ))
    
    officers = query.order_by(PoliceOfficer.name).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('police/officers.html',
                          title='Police Officers',
                          officers=officers,
                          search=search)

@app.route('/police_officers/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_officer():
    form = PoliceOfficerForm()
    
    # Populate dropdown options
    stations = PoliceStation.query.all()
    form.station_id.choices = [(s.id, s.name) for s in stations]
    
    users = User.query.filter(User.role.in_(['admin', 'officer'])).all()
    form.user_id.choices = [(0, 'None')] + [(u.id, u.username) for u in users]
    
    if form.validate_on_submit():
        officer = PoliceOfficer(
            name=form.name.data,
            rank=form.rank.data,
            badge_number=form.badge_number.data,
            contact=form.contact.data,
            station_id=form.station_id.data
        )
        
        if form.user_id.data != 0:
            officer.user_id = form.user_id.data
        
        db.session.add(officer)
        db.session.commit()
        flash('Police officer added successfully!', 'success')
        return redirect(url_for('officer_list'))
    
    return render_template('police/add_officer.html', title='Add Police Officer', form=form)

@app.route('/police_officers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_officer(id):
    officer = PoliceOfficer.query.get_or_404(id)
    form = PoliceOfficerForm()
    
    # Populate dropdown options
    stations = PoliceStation.query.all()
    form.station_id.choices = [(s.id, s.name) for s in stations]
    
    users = User.query.filter(User.role.in_(['admin', 'officer'])).all()
    form.user_id.choices = [(0, 'None')] + [(u.id, u.username) for u in users]
    
    if form.validate_on_submit():
        officer.name = form.name.data
        officer.rank = form.rank.data
        officer.badge_number = form.badge_number.data
        officer.contact = form.contact.data
        officer.station_id = form.station_id.data
        
        if form.user_id.data != 0:
            officer.user_id = form.user_id.data
        else:
            officer.user_id = None
        
        db.session.commit()
        flash('Police officer updated successfully!', 'success')
        return redirect(url_for('officer_list'))
    
    elif request.method == 'GET':
        form.name.data = officer.name
        form.rank.data = officer.rank
        form.badge_number.data = officer.badge_number
        form.contact.data = officer.contact
        form.station_id.data = officer.station_id
        form.user_id.data = officer.user_id if officer.user_id else 0
    
    return render_template('police/add_officer.html', title='Edit Police Officer', form=form)

# Analytics and Reports
@app.route('/crime_statistics')
@login_required
@role_required('analyst')
def crime_statistics():
    # Date range filter
    today = date.today()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        # Default to last 12 months
        start_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
    
    if not end_date:
        end_date = today.strftime('%Y-%m-%d')
    
    # Convert string dates to date objects
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Query crimes within date range
    crimes = Crime.query.filter(Crime.date.between(start_date_obj, end_date_obj)).all()
    
    # Crime types distribution
    crime_types = db.session.query(
        Crime.type, func.count(Crime.id).label('count')
    ).filter(Crime.date.between(start_date_obj, end_date_obj)) \
     .group_by(Crime.type).order_by(desc('count')).all()
    
    # Monthly crime trend
    monthly_crimes = db.session.query(
        extract('year', Crime.date).label('year'),
        extract('month', Crime.date).label('month'),
        func.count(Crime.id).label('count')
    ).filter(Crime.date.between(start_date_obj, end_date_obj)) \
     .group_by('year', 'month').order_by('year', 'month').all()
    
    # Crime locations
    crime_locations = db.session.query(
        Crime.location, func.count(Crime.id).label('count')
    ).filter(Crime.date.between(start_date_obj, end_date_obj)) \
     .group_by(Crime.location).order_by(desc('count')).limit(10).all()
    
    # Format data for charts
    months = []
    counts = []
    
    for mc in monthly_crimes:
        month_name = calendar.month_abbr[int(mc.month)]
        year = int(mc.year)
        months.append(f"{month_name} {year}")
        counts.append(mc.count)
    
    # Crime type labels and data for pie chart
    type_labels = [t.type for t in crime_types]
    type_data = [t.count for t in crime_types]
    
    # Location labels and data for bar chart
    location_labels = [l.location for l in crime_locations]
    location_data = [l.count for l in crime_locations]
    
    # Crime status distribution
    status_data = db.session.query(
        Crime.status, func.count(Crime.id).label('count')
    ).filter(Crime.date.between(start_date_obj, end_date_obj)) \
     .group_by(Crime.status).all()
    
    status_labels = [s.status for s in status_data]
    status_counts = [s.count for s in status_data]
    
    return render_template('reports/crime_statistics.html',
                          title='Crime Statistics',
                          start_date=start_date,
                          end_date=end_date,
                          total_crimes=len(crimes),
                          months=months,
                          counts=counts,
                          type_labels=type_labels,
                          type_data=type_data,
                          location_labels=location_labels,
                          location_data=location_data,
                          status_labels=status_labels,
                          status_counts=status_counts)

@app.route('/crime_map')
@login_required
def crime_map():
    # Get crimes with location coordinates
    crimes = Crime.query.filter(Crime.latitude.isnot(None), Crime.longitude.isnot(None)).all()
    
    # Get police stations with coordinates
    stations = PoliceStation.query.filter(PoliceStation.latitude.isnot(None), PoliceStation.longitude.isnot(None)).all()
    
    return render_template('reports/crime_map.html',
                          title='Crime Map',
                          crimes=crimes,
                          stations=stations)

@app.route('/api/crime_data')
@login_required
def crime_data_api():
    """API endpoint for JSON crime data for mapping"""
    crimes = Crime.query.filter(Crime.latitude.isnot(None), Crime.longitude.isnot(None)).all()
    
    data = [{
        'id': c.id,
        'type': c.type,
        'date': c.date.strftime('%Y-%m-%d'),
        'time': c.time.strftime('%H:%M:%S') if c.time else None,
        'location': c.location,
        'status': c.status,
        'lat': c.latitude,
        'lng': c.longitude
    } for c in crimes]
    
    return jsonify(data)

@app.route('/api/station_data')
@login_required
def station_data_api():
    """API endpoint for JSON police station data for mapping"""
    stations = PoliceStation.query.filter(PoliceStation.latitude.isnot(None), PoliceStation.longitude.isnot(None)).all()
    
    data = [{
        'id': s.id,
        'name': s.name,
        'address': s.address,
        'contact': s.contact,
        'lat': s.latitude,
        'lng': s.longitude
    } for s in stations]
    
    return jsonify(data)

# Error handling routes
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
