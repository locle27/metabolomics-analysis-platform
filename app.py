"""
Metabolomics Flask Application
Based on hotel_flask_app architecture patterns
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, send_file
from dotenv import load_dotenv
import json
from functools import lru_cache
from pathlib import Path
import pandas as pd
from datetime import datetime
import base64
import time
from io import BytesIO
from sqlalchemy import text

# Import models and database service
from models import (
    db, init_db, create_all_tables, get_db_stats,
    LipidClass, MainLipid, AnnotatedIon, ChartSession,
    get_lipids_by_class, get_lipids_by_rt_range, get_multi_ion_lipids, search_lipids
)

# Import chart generation services
from simple_chart_service import SimpleChartGenerator
from dual_chart_service import DualChartService

# Configuration
BASE_DIR = Path(__file__).resolve().parent

# Environment loading
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, template_folder=BASE_DIR / "templates", static_folder=BASE_DIR / "static")
app.secret_key = os.getenv('SECRET_KEY', 'metabolomics-dev-key-change-in-production')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://localhost/metabolomics_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 300,
    'pool_timeout': 30,
    'max_overflow': 20
}

# Initialize database
init_db(app)

# =====================================================
# MAIN DASHBOARD ROUTE
# =====================================================

@app.route('/')
def homepage():
    """University-style homepage with project overview."""
    try:
        # Get basic stats for overview
        stats = get_db_stats(app)
        
        # Get sample recent data
        recent_lipids = MainLipid.query.filter_by(extraction_success=True)\
                                      .order_by(MainLipid.created_at.desc())\
                                      .limit(3).all()
        
        homepage_data = {
            'stats': stats,
            'recent_lipids': [lipid.to_dict() for lipid in recent_lipids],
            'news': [
                {
                    'title': 'New Lipid Database Integration Complete',
                    'date': '2024-12-15',
                    'summary': 'Successfully integrated comprehensive lipid database with over 800+ lipid compounds from Baker Institute.',
                    'image': '/static/news1.jpg'
                },
                {
                    'title': 'Interactive Chart Analysis System Launched', 
                    'date': '2024-12-10',
                    'summary': 'Advanced dual-chart visualization system now available for detailed chromatography analysis.',
                    'image': '/static/news2.jpg'
                }
            ]
        }
        
        return render_template('homepage.html', data=homepage_data)
        
    except Exception as e:
        flash(f'Homepage error: {str(e)}', 'error')
        return render_template('homepage.html', data={'stats': {}, 'recent_lipids': [], 'news': []})

@app.route('/lipid-selection')
def clean_dashboard():
    """Lipid selection page (moved from homepage)."""
    try:
        # Get database statistics
        stats = get_db_stats(app)
        
        # Get all lipids with class information
        lipids = db.session.query(MainLipid)\
                          .join(LipidClass)\
                          .filter(MainLipid.extraction_success == True)\
                          .order_by(LipidClass.class_name, MainLipid.lipid_name)\
                          .all()
        
        # Get class distribution for filter buttons
        class_distribution = db.session.query(
            LipidClass.class_name,
            db.func.count(MainLipid.lipid_id).label('count')
        ).join(MainLipid)\
         .filter(MainLipid.extraction_success == True)\
         .group_by(LipidClass.class_name)\
         .order_by(LipidClass.class_name).all()
        
        # Format data for template
        lipids_data = []
        for lipid in lipids:
            lipid_dict = lipid.to_dict()
            lipid_dict['class_name'] = lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
            lipid_dict['annotated_ions_count'] = len(lipid.annotated_ions)
            lipids_data.append(lipid_dict)
        
        classes_data = []
        for class_name, count in class_distribution:
            classes_data.append({
                'class_name': class_name,
                'count': count
            })
        
        dashboard_data = {
            'stats': stats,
            'lipids': lipids_data,
            'classes': classes_data
        }
        
        return render_template('clean_dashboard.html', data=dashboard_data)
        
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return render_template('clean_dashboard.html', data={'stats': {}, 'lipids': [], 'classes': []})

@app.route('/dashboard-old')
def dashboard():
    """Original dashboard (backup)."""
    try:
        # Get database statistics
        stats = get_db_stats(app)
        
        # Get recent successful extractions
        recent_lipids = MainLipid.query.filter_by(extraction_success=True)\
                                      .order_by(MainLipid.created_at.desc())\
                                      .limit(10).all()
        
        # Get class distribution
        class_distribution = db.session.query(
            LipidClass.class_name,
            db.func.count(MainLipid.lipid_id).label('count')
        ).join(MainLipid).group_by(LipidClass.class_name).all()
        
        # Get multi-ion lipids sample
        multi_ion_sample = get_multi_ion_lipids(limit=5)
        
        dashboard_data = {
            'stats': stats,
            'recent_lipids': [lipid.to_dict() for lipid in recent_lipids],
            'class_distribution': [{'class': cls, 'count': count} for cls, count in class_distribution],
            'multi_ion_sample': [lipid.to_dict() for lipid in multi_ion_sample]
        }
        
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        flash(f'Dashboard error: {str(e)}', 'error')
        return render_template('dashboard.html', data={'stats': {}, 'recent_lipids': [], 'class_distribution': [], 'multi_ion_sample': []})

# =====================================================
# LIPID BROWSING ROUTES
# =====================================================

@app.route('/lipids')
def browse_lipids():
    """Browse and search lipids with filtering."""
    # Get filter parameters
    class_filter = request.args.get('class', '')
    search_term = request.args.get('search', '')
    rt_min = request.args.get('rt_min', type=float)
    rt_max = request.args.get('rt_max', type=float)
    multi_ion_only = request.args.get('multi_ion', type=bool, default=False)
    page = request.args.get('page', 1, type=int)
    per_page = 25
    
    # Build query
    query = MainLipid.query.filter_by(extraction_success=True)
    
    # Apply filters
    if class_filter:
        query = query.join(LipidClass).filter(LipidClass.class_name == class_filter)
    
    if search_term:
        query = query.filter(MainLipid.lipid_name.ilike(f'%{search_term}%'))
    
    if rt_min is not None:
        query = query.filter(MainLipid.retention_time >= rt_min)
    
    if rt_max is not None:
        query = query.filter(MainLipid.retention_time <= rt_max)
    
    if multi_ion_only:
        query = query.join(AnnotatedIon).group_by(MainLipid.lipid_id).having(db.func.count(AnnotatedIon.ion_id) > 1)
    
    # Order and paginate
    query = query.order_by(MainLipid.lipid_name)
    lipids = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get available classes for filter dropdown
    classes = LipidClass.query.order_by(LipidClass.class_name).all()
    
    return render_template('browse_lipids.html', 
                         lipids=lipids, 
                         classes=classes,
                         current_filters={
                             'class': class_filter,
                             'search': search_term,
                             'rt_min': rt_min,
                             'rt_max': rt_max,
                             'multi_ion': multi_ion_only
                         })

@app.route('/lipid/<int:lipid_id>')
def lipid_detail(lipid_id):
    """Show detailed view of a specific lipid."""
    lipid = MainLipid.query.get_or_404(lipid_id)
    
    # Get all annotated ions for this lipid
    annotated_ions = AnnotatedIon.query.filter_by(main_lipid_id=lipid_id)\
                                      .order_by(AnnotatedIon.is_main_lipid.desc(), 
                                               AnnotatedIon.retention_time)\
                                      .all()
    
    lipid_data = {
        'lipid': lipid.to_dict(include_xic=True),
        'annotated_ions': [ion.to_dict() for ion in annotated_ions]
    }
    
    return render_template('lipid_detail.html', data=lipid_data)

# =====================================================
# CHART GENERATION ROUTES
# =====================================================

# NOTE: Old static chart route removed - use optimized-chart-view instead

@app.route('/api/chart-data/<int:lipid_id>')
def api_chart_data(lipid_id):
    """API endpoint to get chart data in JSON format."""
    lipid = MainLipid.query.get_or_404(lipid_id)
    
    selected_ion_ids = request.args.getlist('ions', type=int)
    if not selected_ion_ids:
        selected_ion_ids = [ion.ion_id for ion in lipid.annotated_ions]
    
    rt_window = request.args.get('rt_window', 0.6, type=float)
    
    try:
        chart_generator = MetabolomicsChartGenerator()
        chart_data = chart_generator.get_chart_data_json(
            lipid_id=lipid_id,
            selected_ion_ids=selected_ion_ids,
            rt_window=rt_window
        )
        
        return jsonify({
            'status': 'success',
            'data': chart_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# =====================================================
# MULTI-CHART VIEW ROUTES
# =====================================================

@app.route('/multi-chart-view')
def multi_chart_view():
    """DEPRECATED: Redirects to optimized chart view."""
    flash('Redirected to optimized chart view with improved design.', 'info')
    return redirect(url_for('optimized_chart_view', lipids=request.args.get('lipids', '')))

# =====================================================
# OPTIMIZED INTERACTIVE CHART ROUTES (New Clean Design)
# =====================================================

@app.route('/dual-chart-view') 
def dual_chart_view():
    """Display dual interactive charts (Chart 1: focused, Chart 2: overview) with annotated ions."""
    try:
        # Get selected lipid IDs from query parameters
        lipid_ids_str = request.args.get('lipids', '')
        if not lipid_ids_str:
            flash('No lipids selected for chart view.', 'warning')
            return redirect(url_for('clean_dashboard'))
        
        # Parse lipid IDs
        try:
            selected_lipid_ids = [int(id.strip()) for id in lipid_ids_str.split(',') if id.strip()]
        except ValueError:
            flash('Invalid lipid selection.', 'error')
            return redirect(url_for('clean_dashboard'))
        
        if not selected_lipid_ids:
            flash('No valid lipids selected.', 'warning')
            return redirect(url_for('clean_dashboard'))
        
        # Get selected lipids with their data
        selected_lipids = MainLipid.query.filter(
            MainLipid.lipid_id.in_(selected_lipid_ids)
        ).join(LipidClass).all()
        
        if not selected_lipids:
            flash('Selected lipids not found in database.', 'error')
            return redirect(url_for('clean_dashboard'))
        
        # Format lipids data for template
        lipids_data = []
        for lipid in selected_lipids:
            # Get annotated ions for this lipid
            annotated_ions = AnnotatedIon.query.filter_by(main_lipid_id=lipid.lipid_id).all()
            
            lipid_dict = lipid.to_dict()
            lipid_dict['class_name'] = lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
            lipid_dict['annotated_ions_count'] = len(annotated_ions)
            
            lipids_data.append(lipid_dict)
        
        template_data = {
            'selected_lipids': lipids_data,
            'selected_lipid_ids': selected_lipid_ids
        }
        
        return render_template('dual_chart_view.html', **template_data)
        
    except Exception as e:
        flash(f'Dual chart view error: {str(e)}', 'error')
        return redirect(url_for('clean_dashboard'))

@app.route('/api/dual-chart-data/<int:lipid_id>')
def api_dual_chart_data(lipid_id):
    """API endpoint to get dual chart data (Chart 1 + Chart 2) for Chart.js."""
    try:
        chart_service = DualChartService()
        dual_chart_data = chart_service.get_dual_chart_data(lipid_id)
        
        return jsonify({
            'status': 'success',
            'data': dual_chart_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# =====================================================
# BACKWARD COMPATIBILITY ROUTES
# =====================================================

@app.route('/optimized-chart-view')
def optimized_chart_view():
    """REDIRECT: Use dual-chart-view instead."""
    flash('Redirected to improved dual chart view.', 'info')
    return redirect(url_for('dual_chart_view', lipids=request.args.get('lipids', '')))

# =====================================================
# OLD INTERACTIVE CHART ROUTES (Deprecated)
# =====================================================

@app.route('/interactive-chart-view')
def interactive_chart_view():
    """DEPRECATED: Old interactive chart view. Redirects to optimized version."""
    flash('Redirected to optimized chart view with improved design.', 'info')
    return redirect(url_for('optimized_chart_view', lipids=request.args.get('lipids', '')))

@app.route('/generate-chart/<int:lipid_id>')
def generate_chart(lipid_id):
    """DEPRECATED: Redirect to new dual chart view."""
    return redirect(url_for('dual_chart_view', lipids=str(lipid_id)))

@app.route('/api/generate-chart/<int:lipid_id>')
def api_generate_chart(lipid_id):
    """API endpoint to generate chart for a specific lipid with optional zoom."""
    try:
        lipid = MainLipid.query.get_or_404(lipid_id)
        
        # Chart parameters
        rt_window = request.args.get('rt_window', 0.6, type=float)
        chart_type = request.args.get('chart_type', 'dual')
        
        # Zoom parameters (new feature)
        zoom_start = request.args.get('zoom_start', type=float)
        zoom_end = request.args.get('zoom_end', type=float)
        
        # Get all annotated ions for this lipid
        selected_ion_ids = [ion.ion_id for ion in lipid.annotated_ions]
        
        if not selected_ion_ids:
            return jsonify({
                'status': 'error',
                'message': 'No annotated ions found for this lipid'
            }), 400
        
        # Generate chart using simple chart service
        chart_generator = SimpleChartGenerator()
        
        # Pass zoom parameters if provided
        if zoom_start is not None and zoom_end is not None:
            chart_result = chart_generator.generate_charts_with_zoom(
                lipid_id, zoom_start, zoom_end
            )
        else:
            chart_result = chart_generator.generate_charts(lipid_id)
        
        return jsonify({
            'status': 'success',
            'chart_image': chart_result['chart_image'],
            'metadata': chart_result['metadata']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/chart-data-interactive/<int:lipid_id>')
def api_chart_data_interactive(lipid_id):
    """API endpoint to get interactive chart data for Chart.js."""
    try:
        chart_generator = SimpleChartGenerator()
        chart_data = chart_generator.get_chart_data_json(lipid_id)
        
        return jsonify({
            'status': 'success',
            'data': chart_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/export-charts/<format>')
def api_export_charts(format):
    """API endpoint to export multiple charts."""
    try:
        # Get selected lipid IDs
        lipid_ids_str = request.args.get('lipids', '')
        if not lipid_ids_str:
            return jsonify({'status': 'error', 'message': 'No lipids specified'}), 400
        
        selected_lipid_ids = [int(id.strip()) for id in lipid_ids_str.split(',') if id.strip()]
        
        if format.lower() == 'png':
            # Generate ZIP file with all charts
            import zipfile
            from io import BytesIO
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                chart_generator = SimpleChartGenerator()
                
                for lipid_id in selected_lipid_ids:
                    try:
                        lipid = MainLipid.query.get(lipid_id)
                        if not lipid:
                            continue
                        
                        if not lipid.xic_data:
                            continue
                        
                        chart_result = chart_generator.generate_charts(lipid_id)
                        
                        # Extract base64 image and convert to bytes
                        image_data = chart_result['chart_image'].split(',')[1]
                        image_bytes = base64.b64decode(image_data)
                        
                        # Add to ZIP
                        filename = f"{lipid.lipid_name.replace('/', '_')}_chart.png"
                        zip_file.writestr(filename, image_bytes)
                        
                    except Exception as e:
                        continue
            
            zip_buffer.seek(0)
            
            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name=f'metabolomics_charts_{len(selected_lipid_ids)}_lipids.zip',
                mimetype='application/zip'
            )
        
        else:
            return jsonify({'status': 'error', 'message': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/export-data/<format>')
def api_export_data(format):
    """API endpoint to export lipid data."""
    try:
        # Get selected lipid IDs
        lipid_ids_str = request.args.get('lipids', '')
        if not lipid_ids_str:
            return jsonify({'status': 'error', 'message': 'No lipids specified'}), 400
        
        selected_lipid_ids = [int(id.strip()) for id in lipid_ids_str.split(',') if id.strip()]
        
        # Get lipids data
        selected_lipids = MainLipid.query.filter(
            MainLipid.lipid_id.in_(selected_lipid_ids)
        ).join(LipidClass).all()
        
        if format.lower() == 'csv':
            import csv
            from io import StringIO
            
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            
            # Write header
            writer.writerow([
                'Lipid ID', 'Lipid Name', 'Class', 'Retention Time (min)', 
                'Precursor Ion', 'Product Ion', 'Collision Energy', 
                'Polarity', 'Annotated Ions Count', 'API Code'
            ])
            
            # Write data
            for lipid in selected_lipids:
                writer.writerow([
                    lipid.lipid_id,
                    lipid.lipid_name,
                    lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown',
                    lipid.retention_time,
                    lipid.precursor_ion,
                    lipid.product_ion,
                    lipid.collision_energy,
                    lipid.polarity,
                    len(lipid.annotated_ions),
                    lipid.api_code
                ])
            
            csv_buffer.seek(0)
            
            return Response(
                csv_buffer.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=metabolomics_data_{len(selected_lipid_ids)}_lipids.csv'}
            )
            
        elif format.lower() == 'json':
            lipids_data = []
            for lipid in selected_lipids:
                lipid_dict = lipid.to_dict(include_xic=True)
                lipid_dict['class_name'] = lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
                lipid_dict['annotated_ions'] = [ion.to_dict() for ion in lipid.annotated_ions]
                lipids_data.append(lipid_dict)
            
            return jsonify({
                'status': 'success',
                'export_timestamp': datetime.now().isoformat(),
                'lipid_count': len(lipids_data),
                'lipids': lipids_data
            })
        
        else:
            return jsonify({'status': 'error', 'message': 'Unsupported format'}), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# =====================================================
# MANAGE LIPIDS ROUTES
# =====================================================

@app.route('/manage-lipids')
def manage_lipids():
    """Manage lipids interface with detailed data view."""
    try:
        # Get database statistics
        stats = get_db_stats(app)
        
        # Get ALL lipids with class information (no pagination for chart generation)
        lipids_query = db.session.query(MainLipid)\
                                 .outerjoin(LipidClass)\
                                 .order_by(LipidClass.class_name.nullslast(), MainLipid.lipid_name)
        
        # Get total count
        total_count = lipids_query.count()
        
        # Get ALL results (no pagination)
        all_lipids = lipids_query.all()
        
        # Get class distribution
        class_distribution = db.session.query(
            LipidClass.class_name,
            db.func.count(MainLipid.lipid_id).label('count')
        ).join(MainLipid)\
         .group_by(LipidClass.class_name)\
         .order_by(LipidClass.class_name).all()
        
        # Format data for template
        lipids_data = []
        for lipid in all_lipids:
            lipid_dict = lipid.to_dict()
            lipid_dict['class_name'] = lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
            lipid_dict['annotated_ions_count'] = len(lipid.annotated_ions)
            lipids_data.append(lipid_dict)
        
        classes_data = []
        for class_name, count in class_distribution:
            classes_data.append({
                'class_name': class_name,
                'count': count
            })
        
        # Calculate additional stats
        successful_extractions = MainLipid.query.filter_by(extraction_success=True).count()
        stats['successful_extractions'] = successful_extractions
        
        manage_data = {
            'stats': stats,
            'lipids': lipids_data,
            'classes': classes_data,
            'total_count': total_count
        }
        
        return render_template('manage_lipids.html', data=manage_data)
        
    except Exception as e:
        flash(f'Management interface error: {str(e)}', 'error')
        return render_template('manage_lipids.html', data={'stats': {}, 'lipids': [], 'classes': [], 'total_count': 0})

@app.route('/api/lipid-ions/<int:lipid_id>')
def api_lipid_ions(lipid_id):
    """API endpoint to get annotated ions for a specific lipid."""
    try:
        lipid = MainLipid.query.get_or_404(lipid_id)
        
        # Get all annotated ions for this lipid
        annotated_ions = AnnotatedIon.query.filter_by(main_lipid_id=lipid_id)\
                                          .order_by(AnnotatedIon.is_main_lipid.desc(), 
                                                   AnnotatedIon.retention_time)\
                                          .all()
        
        ions_data = [ion.to_dict() for ion in annotated_ions]
        
        return jsonify({
            'status': 'success',
            'lipid_id': lipid_id,
            'lipid_name': lipid.lipid_name,
            'ions_count': len(ions_data),
            'ions': ions_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/lipid-xic-summary/<int:lipid_id>')
def api_lipid_xic_summary(lipid_id):
    """API endpoint to get XIC data summary for a specific lipid."""
    try:
        lipid = MainLipid.query.get_or_404(lipid_id)
        
        xic_summary = None
        
        if lipid.xic_data:
            # Parse XIC data to get summary
            xic_data = lipid.xic_data
            
            if isinstance(xic_data, str):
                try:
                    xic_data = json.loads(xic_data)
                except:
                    pass
            
            if isinstance(xic_data, dict):
                # Create summary from available data
                xic_summary = {
                    'data_type': type(xic_data).__name__,
                    'has_time_series': 'time' in xic_data and 'intensity' in xic_data,
                    'has_points': 'points' in xic_data,
                    'has_stats': any(key in xic_data for key in ['data_points', 'max_intensity', 'min_intensity', 'avg_intensity'])
                }
                
                # Add available statistics
                for key in ['data_points', 'max_intensity', 'min_intensity', 'avg_intensity']:
                    if key in xic_data:
                        xic_summary[key] = xic_data[key]
                
                # Add time/intensity info if available
                if 'time' in xic_data and 'intensity' in xic_data:
                    xic_summary['time_points'] = len(xic_data['time'])
                    xic_summary['intensity_points'] = len(xic_data['intensity'])
                elif 'points' in xic_data:
                    xic_summary['points_count'] = len(xic_data['points'])
        
        return jsonify({
            'status': 'success',
            'lipid_id': lipid_id,
            'lipid_name': lipid.lipid_name,
            'has_xic_data': lipid.xic_data is not None,
            'xic_summary': xic_summary
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# =====================================================
# DATA MANAGEMENT ROUTES
# =====================================================

# Note: Data loading functionality removed - data is now pre-imported via import_hybrid_database.py

@app.route('/admin/stats')
def admin_stats():
    """Admin statistics and database health."""
    try:
        stats = get_db_stats(app)
        
        # Additional detailed stats
        detailed_stats = {}
        
        # Class distribution with percentages
        class_dist = db.session.query(
            LipidClass.class_name,
            db.func.count(MainLipid.lipid_id).label('count')
        ).join(MainLipid).group_by(LipidClass.class_name).all()
        
        total_lipids = sum([count for _, count in class_dist])
        detailed_stats['class_distribution'] = [
            {
                'class': cls, 
                'count': count, 
                'percentage': round(count/total_lipids*100, 1) if total_lipids > 0 else 0
            } 
            for cls, count in class_dist
        ]
        
        # Recent activity
        recent_sessions = ChartSession.query.order_by(ChartSession.session_timestamp.desc()).limit(10).all()
        detailed_stats['recent_sessions'] = [session.to_dict() for session in recent_sessions]
        
        # Data quality metrics
        lipids_with_xic = MainLipid.query.filter(MainLipid.xic_data.isnot(None)).count()
        detailed_stats['data_quality'] = {
            'lipids_with_xic_data': lipids_with_xic,
            'xic_coverage_percentage': round(lipids_with_xic/total_lipids*100, 1) if total_lipids > 0 else 0
        }
        
        return render_template('admin_stats.html', stats=stats, detailed_stats=detailed_stats)
        
    except Exception as e:
        flash(f'Statistics error: {str(e)}', 'error')
        return render_template('admin_stats.html', stats={}, detailed_stats={})

# =====================================================
# API ROUTES
# =====================================================

@app.route('/api/lipids')
def api_lipids():
    """API endpoint for lipids with filtering."""
    class_name = request.args.get('class')
    search = request.args.get('search')
    limit = request.args.get('limit', 50, type=int)
    
    query = MainLipid.query.filter_by(extraction_success=True)
    
    if class_name:
        query = query.join(LipidClass).filter(LipidClass.class_name == class_name)
    
    if search:
        query = query.filter(MainLipid.lipid_name.ilike(f'%{search}%'))
    
    lipids = query.limit(limit).all()
    
    return jsonify({
        'status': 'success',
        'count': len(lipids),
        'lipids': [lipid.to_dict() for lipid in lipids]
    })

@app.route('/api/classes')
def api_classes():
    """API endpoint for lipid classes."""
    classes = LipidClass.query.order_by(LipidClass.class_name).all()
    return jsonify({
        'status': 'success',
        'classes': [cls.to_dict() for cls in classes]
    })

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# =====================================================
# APPLICATION STARTUP
# =====================================================

def create_app():
    """Application factory pattern."""
# =====================================================
# ADMIN ROUTES - Google OAuth Authentication System
# =====================================================

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard - requires authentication (future)."""
    try:
        # For now, show basic admin interface
        # TODO: Add Google OAuth authentication
        
        stats = get_db_stats(app)
        
        # Get system information
        admin_info = {
            'total_users': 0,  # Placeholder for future user system
            'active_sessions': 0,  # Placeholder
            'system_status': 'Operational',
            'database_status': 'Connected',
            'last_backup': 'Not configured',
            'features_available': [
                'Lipid Database Management',
                'Chart Generation System', 
                'Data Export Tools',
                'Statistics Dashboard'
            ],
            'planned_features': [
                'Google OAuth Authentication',
                'User Management System',
                'Advanced Analytics',
                'API Access Control',
                'Automated Backups'
            ]
        }
        
        return render_template('admin_dashboard.html', stats=stats, admin_info=admin_info)
        
    except Exception as e:
        flash(f'Admin dashboard error: {str(e)}', 'error')
        return render_template('admin_dashboard.html', stats={}, admin_info={})

@app.route('/admin/login')
def admin_login():
    """Admin login page - Google OAuth (placeholder)."""
    # TODO: Implement Google OAuth
    return render_template('admin_login.html', 
                         oauth_url='#google-oauth-placeholder',
                         message='Google OAuth integration coming soon!')

@app.route('/admin/users')
def admin_users():
    """Admin user management (placeholder)."""
    # TODO: Implement user management
    users_info = {
        'total_users': 0,
        'active_users': 0,
        'pending_registrations': 0,
        'user_roles': ['Admin', 'Researcher', 'Viewer'],
        'recent_logins': []
    }
    return render_template('admin_users.html', users_info=users_info)

@app.route('/admin/system')
def admin_system():
    """Admin system settings (placeholder)."""
    system_info = {
        'version': '1.0.0',
        'uptime': 'Unknown',
        'memory_usage': 'Unknown',
        'database_size': 'Unknown',
        'backup_status': 'Not configured',
        'oauth_status': 'Not configured'
    }
    return render_template('admin_system.html', system_info=system_info)

    return app

if __name__ == '__main__':
    # Create tables if they don't exist
    with app.app_context():
        try:
            create_all_tables(app)
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Database setup error: {e}")
    
    # Run application
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    print(f"🚀 Starting Metabolomics Flask App on port {port}")
    print(f"   Debug mode: {debug_mode}")
    print(f"   Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)