"""
Optimized Chart Service - Clean Interactive Charts
Matches the reference chart.png design with:
- Clean chromatogram without labels
- Y-axis starting from 0
- Clickable peaks with detailed popups
- Proper intensity scaling
"""

import json
from typing import Dict, List, Optional, Tuple, Any
from models import db, MainLipid, AnnotatedIon

class OptimizedChartService:
    """
    Optimized chart service for clean, interactive charts.
    Returns data for Chart.js with clickable peak functionality.
    """
    
    def __init__(self):
        # Color mapping for different annotation types
        self.annotation_colors = {
            'Current lipid': '#1f77b4',      # Blue
            '+2 isotope': '#d62728',         # Red  
            'Similar MRM': '#ff7f0e',        # Orange
            'Default': '#2ca02c'             # Green
        }
        
        # Integration area color (light blue/green like reference)
        self.integration_color = 'rgba(31, 119, 180, 0.3)'  # Light blue with transparency
    
    def get_lipid_chart_data(self, lipid_id: int) -> Dict[str, Any]:
        """
        Get dual chart data for a specific lipid in Chart.js format.
        Returns both Chart 1 (focused RT±0.6) and Chart 2 (full 0-16 min overview)
        with annotated ions displayed on charts and clickable peak information.
        """
        try:
            # Get lipid with annotated ions
            lipid = MainLipid.query.get(lipid_id)
            if not lipid:
                raise ValueError(f"Lipid with ID {lipid_id} not found")
            
            # Get XIC data from database
            xic_data = lipid.xic_data
            if not xic_data:
                raise ValueError(f"No XIC data found for lipid {lipid.lipid_name}")
            
            # Parse XIC data
            time_points = []
            intensity_points = []
            
            if isinstance(xic_data, list):
                for point in xic_data:
                    if isinstance(point, dict) and 'time' in point and 'intensity' in point:
                        time_points.append(float(point['time']))
                        intensity_points.append(float(point['intensity']))
            
            if not time_points:
                raise ValueError("Invalid XIC data format")
            
            # Get all annotated ions for this lipid
            annotated_ions = AnnotatedIon.query.filter_by(main_lipid_id=lipid_id).all()
            
            # Find main lipid retention time for Chart 1 range
            main_retention_time = lipid.retention_time
            if not main_retention_time and annotated_ions:
                # Use first annotated ion RT if main lipid RT not available
                main_retention_time = annotated_ions[0].retention_time
            
            if not main_retention_time:
                raise ValueError("No retention time found for chart range calculation")
            
            # Calculate Chart 1 range (RT ± 0.6 minutes)
            chart1_start = max(0.0, float(main_retention_time) - 0.6)
            chart1_end = float(main_retention_time) + 0.6
            
            # Build dual chart data
            chart1_data = self._create_chart_config(
                time_points, intensity_points, annotated_ions, 
                chart1_start, chart1_end, "Chart 1: Focused View"
            )
            
            chart2_data = self._create_chart_config(
                time_points, intensity_points, annotated_ions,
                0.0, 16.0, "Chart 2: Full Overview"
            )
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'interaction': {
                        'intersect': False,
                        'mode': 'index'
                    },
                    'plugins': {
                        'legend': {
                            'display': False  # Hide legend for clean look
                        },
                        'tooltip': {
                            'enabled': True,
                            'backgroundColor': 'rgba(255, 255, 255, 0.95)',
                            'titleColor': '#333',
                            'bodyColor': '#333',
                            'borderColor': '#ccc',
                            'borderWidth': 1,
                            'cornerRadius': 6,
                            'displayColors': False,
                            'callbacks': {
                                'title': 'function(context) { return "RT: " + context[0].parsed.x.toFixed(2) + " min"; }',
                                'label': 'function(context) { return "Intensity: " + context.parsed.y.toFixed(0); }'
                            }
                        }
                    },
                    'scales': {
                        'x': {
                            'type': 'linear',
                            'position': 'bottom',
                            'title': {
                                'display': True,
                                'text': 'Retention time (minutes)',
                                'font': {'size': 12, 'weight': 'bold'}
                            },
                            'grid': {
                                'color': 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        'y': {
                            'beginAtZero': True,  # IMPORTANT: Start Y-axis from 0
                            'title': {
                                'display': True,
                                'text': 'Intensity',
                                'font': {'size': 12, 'weight': 'bold'}
                            },
                            'grid': {
                                'color': 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    },
                    'onClick': 'handleChartClick'  # Custom click handler
                }
            }
            
            # Add integration areas and clickable peak data
            peak_annotations = []
            clickable_peaks = []
            
            for ion in annotated_ions:
                if ion.retention_time and ion.int_start and ion.int_end:
                    # Create integration area data
                    integration_area = self._create_integration_area(
                        time_points, intensity_points,
                        ion.int_start, ion.int_end, ion.retention_time
                    )
                    
                    if integration_area:
                        chart_data['data']['datasets'].append(integration_area)
                    
                    # Create clickable peak info
                    peak_info = {
                        'lipid_name': ion.ion_lipid_name,
                        'lipid_class': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown',
                        'retention_time': round(float(ion.retention_time), 2),
                        'integration_start': round(float(ion.int_start), 2),
                        'integration_end': round(float(ion.int_end), 2),
                        'precursor_mass': ion.precursor_ion or 'N/A',
                        'product_mass': ion.product_ion or 'N/A',
                        'annotation_type': ion.annotation_type or 'Similar MRM',
                        'rt_window': [ion.int_start, ion.int_end],
                        'color': self.annotation_colors.get(ion.annotation_type, self.annotation_colors['Default'])
                    }
                    clickable_peaks.append(peak_info)
            
            # Add metadata
            result = {
                'chart_config': chart_data,
                'lipid_info': {
                    'lipid_id': lipid.lipid_id,
                    'lipid_name': lipid.lipid_name,
                    'api_code': lipid.api_code,
                    'class_name': lipid.lipid_class.class_name if lipid.lipid_class else 'Unknown'
                },
                'clickable_peaks': clickable_peaks,
                'annotated_ions_count': len(annotated_ions)
            }
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error generating chart data: {str(e)}")
    
    def _create_integration_area(self, time_points: List[float], intensity_points: List[float], 
                               int_start: float, int_end: float, retention_time: float) -> Optional[Dict]:
        """
        Create integration area dataset for Chart.js.
        Shows the filled area between integration boundaries.
        """
        try:
            # Find data points within integration window
            integration_data = []
            
            for i, time in enumerate(time_points):
                if int_start <= time <= int_end:
                    integration_data.append({
                        'x': time,
                        'y': intensity_points[i]
                    })
            
            if not integration_data:
                return None
            
            # Add boundary points at baseline (y=0) for proper fill
            integration_data.insert(0, {'x': int_start, 'y': 0})
            integration_data.append({'x': int_end, 'y': 0})
            
            return {
                'label': 'Integration Area',
                'data': integration_data,
                'borderColor': 'rgba(31, 119, 180, 0.8)',  # Blue border
                'backgroundColor': self.integration_color,   # Light blue fill
                'borderWidth': 1,
                'fill': True,
                'pointRadius': 0,
                'pointHoverRadius': 0,
                'order': 1  # Draw behind main chromatogram
            }
            
        except Exception as e:
            print(f"Warning: Could not create integration area: {e}")
            return None
    
    def get_multiple_lipids_chart_data(self, lipid_ids: List[int]) -> Dict[str, Any]:
        """
        Get chart data for multiple lipids.
        Each lipid gets its own chart panel.
        """
        results = {}
        
        for lipid_id in lipid_ids:
            try:
                chart_data = self.get_lipid_chart_data(lipid_id)
                results[str(lipid_id)] = chart_data
            except Exception as e:
                print(f"Error getting chart data for lipid {lipid_id}: {e}")
                results[str(lipid_id)] = {'error': str(e)}
        
        return results
    
    def get_annotated_ions_table_data(self, lipid_id: int) -> List[Dict[str, Any]]:
        """
        Get annotated ions data for the bottom table (like in reference image).
        """
        try:
            annotated_ions = AnnotatedIon.query.filter_by(main_lipid_id=lipid_id).all()
            
            table_data = []
            for ion in annotated_ions:
                row = {
                    'ion_id': ion.ion_id,
                    'lipid_name': ion.ion_lipid_name,
                    'annotation_type': ion.annotation_type or 'Similar MRM',
                    'retention_time': round(float(ion.retention_time), 2) if ion.retention_time else 'N/A',
                    'precursor_ion': ion.precursor_ion or 'N/A',
                    'product_ion': ion.product_ion or 'N/A',
                    'integration_start': round(float(ion.int_start), 2) if ion.int_start else 'N/A',
                    'integration_end': round(float(ion.int_end), 2) if ion.int_end else 'N/A',
                    'collision_energy': ion.collision_energy or 'N/A',
                    'is_main': ion.is_main_lipid
                }
                table_data.append(row)
            
            return sorted(table_data, key=lambda x: x['is_main'], reverse=True)
            
        except Exception as e:
            print(f"Error getting annotated ions data: {e}")
            return []