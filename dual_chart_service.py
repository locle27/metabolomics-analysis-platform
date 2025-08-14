"""
Dual Chart Service - Corrected Interactive Charts
Shows both Chart 1 (focused RT±0.6) and Chart 2 (full 0-16 min overview)
with annotated ions displayed ON the charts and proper mouse hover information
"""

import json
import math
from typing import Dict, List, Optional, Tuple, Any
from models_sqlite import fast_db, MainLipid, AnnotatedIon

class DualChartService:
    """
    Dual chart service for interactive charts with annotated ions.
    Returns data for Chart.js with proper hover information and dual chart display.
    """
    
    def __init__(self):
        # Color mapping for different annotation types (updated user request)
        self.annotation_colors = {
            'Current lipid': '#1f77b4',      # Blue
            '+2 isotope': '#ff4757',         # Light Red (user requested)
            'Similar MRM': '#2ed573',        # Light Green (user requested)  
            'Default': '#40E0D0'             # Turquoise/cyan (like reference image)
        }
        
        # Integration area color (light blue like reference)
        self.integration_color = 'rgba(31, 119, 180, 0.3)'
    
    def get_dual_chart_data(self, lipid_id: int) -> Dict[str, Any]:
        """
        Get dual chart data for a specific lipid.
        Returns both Chart 1 (focused) and Chart 2 (overview) with annotated ions.
        """
        try:
            # Get lipid with annotated ions using SQLite
            chart_data = fast_db.get_lipid_chart_data(lipid_id)
            if not chart_data:
                raise ValueError(f"Lipid with ID {lipid_id} not found")
            
            lipid_info = chart_data['lipid_info']
            annotated_ions_data = chart_data['annotated_ions']
            xic_data = chart_data['xic_data']
            
            if not xic_data:
                raise ValueError(f"No XIC data found for lipid {lipid_info['lipid_name']}")
            
            # Parse XIC data with error handling
            time_points = []
            intensity_points = []
            
            # Handle XIC data from Railway (now matches web-lipid2 format exactly)
            if isinstance(xic_data, list):
                # Railway JSON parsed to list - exact format from web-lipid2
                for point in xic_data:
                    if isinstance(point, dict) and 'time' in point and 'intensity' in point:
                        try:
                            time_val = float(point['time'])
                            intensity_val = float(point['intensity'])
                            if not (math.isnan(time_val) or math.isnan(intensity_val)):
                                time_points.append(time_val)
                                intensity_points.append(intensity_val)
                        except (ValueError, TypeError):
                            continue
            elif isinstance(xic_data, str):
                # String format - parse as JSON to get list
                try:
                    parsed_json = json.loads(xic_data)
                    if isinstance(parsed_json, list):
                        for point in parsed_json:
                            if isinstance(point, dict) and 'time' in point and 'intensity' in point:
                                try:
                                    time_val = float(point['time'])
                                    intensity_val = float(point['intensity'])
                                    if not (math.isnan(time_val) or math.isnan(intensity_val)):
                                        time_points.append(time_val)
                                        intensity_points.append(intensity_val)
                                except (ValueError, TypeError):
                                    continue
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"WARNING: JSON parsing error for {lipid_info['lipid_name']}: {e}")
            
            if not time_points:
                raise ValueError("No valid XIC data points found")
            
            print(f"DEBUG: Loaded {len(time_points)} XIC data points")
            
            # Convert annotated ions data to objects for compatibility
            annotated_ions = []
            for ion_data in annotated_ions_data:
                ion_obj = type('AnnotatedIon', (), ion_data)()
                annotated_ions.append(ion_obj)
            
            # Find main lipid retention time for Chart 1 range
            main_retention_time = lipid_info.get('retention_time')
            if not main_retention_time and annotated_ions:
                # Use first annotated ion RT if main lipid RT not available
                main_retention_time = annotated_ions[0].retention_time
            
            if not main_retention_time:
                raise ValueError("No retention time found for chart range calculation")
            
            # Calculate Chart 1 range (RT ± 0.6 minutes) - EXACT FORMULA
            chart1_start = max(0.0, float(main_retention_time) - 0.6)
            chart1_end = float(main_retention_time) + 0.6
            
            # Create both charts
            chart1_config = self._create_chart_config(
                time_points, intensity_points, annotated_ions, 
                chart1_start, chart1_end, 
                f"Chart 1: {lipid_info['lipid_name']} - Focused View (RT ± 0.6 min)"
            )
            
            chart2_config = self._create_chart_config(
                time_points, intensity_points, annotated_ions,
                0.0, 16.0, 
                f"Chart 2: {lipid_info['lipid_name']} - Full Overview (0-16 min)",
                force_x_range=True  # Force exact 0-16 range for Chart 2
            )
            
            # Prepare result
            result = {
                'lipid_info': {
                    'lipid_id': lipid_info['lipid_id'],
                    'lipid_name': lipid_info['lipid_name'],
                    'api_code': lipid_info.get('api_code', ''),
                    'class_name': lipid_info.get('class_name', 'Unknown'),
                    'retention_time': float(main_retention_time),
                    'chart1_range': f"{chart1_start:.1f} - {chart1_end:.1f} min",
                    'chart2_range': "0.0 - 16.0 min"
                },
                'chart1': chart1_config,
                'chart2': chart2_config,
                'annotated_ions_count': len(annotated_ions),
                'annotated_ions': [self._format_ion_data(ion) for ion in annotated_ions]
            }
            
            return result
            
        except Exception as e:
            import traceback
            print(f"FULL ERROR: {traceback.format_exc()}")
            raise ValueError(f"Error generating dual chart data: {str(e)}")
    
    def _get_parent_lipid(self, ion):
        """Get the parent lipid object for extracting class information."""
        try:
            # For SQLite compatibility, return a simple object with class info
            if hasattr(ion, 'main_lipid_id'):
                chart_data = fast_db.get_lipid_chart_data(ion.main_lipid_id)
                if chart_data:
                    class_info = type('LipidClass', (), {'class_name': chart_data['lipid_info'].get('class_name', 'Unknown')})()
                    parent = type('MainLipid', (), {'lipid_class': class_info})()
                    return parent
            return None
        except Exception:
            return None
    
    def _create_chart_config(self, time_points: List[float], intensity_points: List[float], 
                           annotated_ions: List, x_min: float, x_max: float, title: str, force_x_range: bool = False) -> Dict:
        """
        Create Chart.js configuration for a single chart with proper hover and annotations.
        
        Y-axis scaling algorithm:
        - Always starts from 0 (no gaps)
        - Uses smaller step sizes to bring data points closer to 0
        - Example: If min=40, uses steps of 5: 0, 5, 10, 15, 20, 25, 30, 35, 40, 45...
        - Makes charts more visually appealing with data close to baseline
        """
        
        # Filter data to chart range
        filtered_data = []
        filtered_intensities = []
        for i, time in enumerate(time_points):
            if x_min <= time <= x_max:
                filtered_data.append({'x': time, 'y': intensity_points[i]})
                filtered_intensities.append(intensity_points[i])
        
        # Calculate optimized Y-axis range - ALWAYS start from 0
        if filtered_intensities:
            min_intensity = min(filtered_intensities)
            max_intensity = max(filtered_intensities)
            
            print(f"DEBUG: Chart range {x_min}-{x_max}, Min: {min_intensity}, Max: {max_intensity}")
            
            # Y-axis ALWAYS starts from 0 (as requested)
            y_min = 0
            
            # Set y_max with reasonable round number above highest peak
            # Don't need exact precision - just easy-to-read scale
            if max_intensity <= 100:
                y_max = ((int(max_intensity) // 10) + 1) * 10  # Round up to nearest 10
            elif max_intensity <= 500:
                y_max = ((int(max_intensity) // 25) + 1) * 25  # Round up to nearest 25
            else:
                y_max = ((int(max_intensity) // 50) + 1) * 50  # Round up to nearest 50
            
            # EXTREME Y-AXIS COMPRESSION: Bring data ALMOST TO 0
            # Goal: If lowest point is 40, it should appear almost touching 0
            # No proportional spacing - just make it visually close
            
            print(f"DEBUG: Min: {min_intensity}, Max: {max_intensity}, Y_max: {y_max}")
            
            # Safety check: ensure we have valid data
            if y_max <= 0 or max_intensity <= 0:
                print(f"WARNING: Invalid data range, using fallback")
                calculated_step_size = 10
                y_min = 0
            else:
                # RADICAL APPROACH: Start Y-axis VERY close to lowest data point
                # Make the lowest point appear almost at 0 with minimal gap
                
                # Set y_min to be very close to min_intensity (tiny gap)
                gap_percentage = 0.02  # Only 2% gap below lowest point
                y_min = max(0, min_intensity - (min_intensity * gap_percentage))
                
                # If lowest point is small, start from 0
                if min_intensity < 10:
                    y_min = 0
                
                # Calculate range from this compressed start point
                compressed_range = y_max - y_min
                
                # Use step sizes based on the compressed range
                if compressed_range >= 1000:
                    step_size = 100
                elif compressed_range >= 500:
                    step_size = 50
                elif compressed_range >= 200:
                    step_size = 25
                elif compressed_range >= 100:
                    step_size = 10
                elif compressed_range >= 50:
                    step_size = 5
                else:
                    step_size = max(1, int(compressed_range / 10))
                
                # CRITICAL: Ensure step_size is never zero to prevent division by zero
                if step_size <= 0:
                    step_size = 1
                    print(f"WARNING: Step size was <= 0, forced to 1")
                
                # Validate: ensure reasonable number of total ticks
                try:
                    total_ticks = int(y_max / step_size) + 1
                    if total_ticks > 15:
                        # If too many ticks, double the step size
                        step_size = max(step_size * 2, 1)  # Ensure minimum 1
                        total_ticks = int(y_max / step_size) + 1
                        if total_ticks > 15:
                            # If still too many, use magnitude-based calculation
                            step_size = max(int(y_max / 10), 1)  # Ensure minimum 1
                            if step_size < 10:
                                step_size = 10
                            elif step_size < 50:
                                step_size = 50
                            else:
                                step_size = max(int(step_size / 100) * 100, 100)  # Round to nearest 100, min 100
                except (ZeroDivisionError, ValueError) as e:
                    print(f"ERROR in tick calculation: {e}, using fallback step_size = 10")
                    step_size = 10
                
                # Final safety check
                calculated_step_size = max(int(step_size), 1)  # Absolute minimum is 1
                
                print(f"DEBUG: Step size: {calculated_step_size}, Total ticks: {int(y_max/calculated_step_size)+1 if calculated_step_size > 0 else 'N/A'}")
                # Calculate how close to 0 the data will appear
                ticks_to_data = min_intensity / calculated_step_size if calculated_step_size > 0 else 0
                print(f"DEBUG: Data appears {ticks_to_data:.1f} ticks from 0, lowest point at ~{min_intensity:.1f}, step size: {calculated_step_size}")
                print(f"DEBUG: Tick sequence: 0, {calculated_step_size}, {calculated_step_size*2}, {calculated_step_size*3}... (data at ~{min_intensity:.1f})")
            
        else:
            print(f"WARNING: No filtered intensities found, using fallback values")
            y_min, y_max = 0, 100  # Fallback values
            calculated_step_size = 10
        
        # Base datasets - main chromatogram line (like reference image)
        datasets = [
            {
                'label': 'Chromatogram',
                'data': filtered_data,
                'borderColor': '#1f77b4',  # Blue line
                'backgroundColor': 'rgba(0, 0, 0, 0)',  # Transparent
                'borderWidth': 1.2,  # Slightly thinner for cleaner look
                'fill': False,
                'pointRadius': 0,  # Clean line without markers
                'pointHoverRadius': 4,
                'pointHoverBackgroundColor': '#1f77b4',
                'tension': 0.0,  # No smoothing for accurate data representation
                'order': 2  # Draw behind annotations
            }
        ]
        
        # Add annotated ion datasets (only integration areas with targeted hover info)
        # Find the main/current lipid for boundary display
        main_lipid_ion = None
        for ion in annotated_ions:
            if ion.annotation_type == 'Current lipid' or ion.is_main_lipid:
                main_lipid_ion = ion
                break
        
        # If no explicit main lipid found, use the first one
        if not main_lipid_ion and annotated_ions:
            main_lipid_ion = annotated_ions[0]
        
        # Determine if this is Chart 2 (full range 0-16) for boundary line logic
        is_chart2 = (x_min == 0.0 and x_max == 16.0)
        
        for idx, ion in enumerate(annotated_ions):
            if ion.retention_time and ion.int_start and ion.int_end:
                # Only add if ion is within chart range
                if x_min <= float(ion.retention_time) <= x_max:
                    
                    # CHART-SPECIFIC FILTERING:
                    should_add_ion = False
                    
                    if is_chart2:
                        # Chart 2: Show all types (Current lipid, isotopes, Similar MRM)
                        should_add_ion = True
                    else:
                        # Chart 1: ONLY show current/main lipid (no isotopes or Similar MRM)
                        should_add_ion = (ion == main_lipid_ion)
                    
                    if should_add_ion:
                        # Add INDIVIDUAL integration area with SPECIFIC hover info for THIS ion only
                        integration_area = self._create_integration_area(
                            time_points, intensity_points, 
                            float(ion.int_start), float(ion.int_end),
                            ion, x_min, x_max, self._get_parent_lipid(ion), idx
                        )
                        if integration_area:
                            datasets.append(integration_area)
                    
                    # Add vertical dashed lines logic:
                    if ion == main_lipid_ion:
                        if is_chart2:
                            # Chart 2: Show boundaries according to Chart 1 range (RT ± 0.6)
                            main_rt = float(main_lipid_ion.retention_time)
                            chart1_start = max(0.0, main_rt - 0.6)
                            chart1_end = main_rt + 0.6
                            
                            # Use Chart 1 range for boundaries in Chart 2
                            boundary_lines = self._create_integration_boundary_lines(
                                chart1_start, chart1_end, y_max, ion, idx
                            )
                            datasets.extend(boundary_lines)
                        else:
                            # Chart 1: Show boundaries for current lipid integration range
                            boundary_lines = self._create_integration_boundary_lines(
                                float(ion.int_start), float(ion.int_end), y_max, ion, idx
                            )
                            datasets.extend(boundary_lines)
        
        # Chart configuration
        config = {
            'type': 'line',
            'data': {'datasets': datasets},
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title,
                        'font': {'size': 14, 'weight': 'bold'}
                    },
                    'legend': {
                        'display': False,  # Hide individual chart legends
                        'position': 'top'
                    },
                    'tooltip': {
                        'enabled': True,
                        'backgroundColor': 'rgba(255, 255, 255, 0.95)',
                        'titleColor': '#333',
                        'bodyColor': '#333',
                        'borderColor': '#ccc',
                        'borderWidth': 1,
                        'cornerRadius': 6,
                        'displayColors': True
                    }
                },
                'scales': {
                    'x': {
                        'type': 'linear',
                        'position': 'bottom',
                        'min': 0.0 if force_x_range else x_min,  # Always start at 0 for Chart 2
                        'max': 16.0 if force_x_range else x_max,  # Always end at 16 for Chart 2
                        'title': {
                            'display': True,
                            'text': 'Retention time (minutes)',
                            'font': {'size': 12, 'weight': 'bold'}
                        },
                        'grid': {'color': 'rgba(0, 0, 0, 0.1)'},
                        'ticks': {
                            'stepSize': 1,  # FORCE 1-unit intervals: 0, 1, 2, 3, 4...
                            'maxTicksLimit': 20  # Allow enough ticks for 1-unit steps
                        }
                    },
                    'y': {
                        'min': y_min,  # Dynamic minimum for proper scaling
                        'max': y_max,  # Optimized maximum to make data prominent
                        'title': {
                            'display': True,
                            'text': 'Intensity',
                            'font': {'size': 12, 'weight': 'bold'}
                        },
                        'grid': {'color': 'rgba(0, 0, 0, 0.1)'},
                        'ticks': {
                            'stepSize': max(calculated_step_size, 1),  # Minimum step of 1
                            'maxTicksLimit': 15,  # Reasonable number of ticks
                            'beginAtZero': False,  # Don't force zero - use our custom min
                            'min': y_min,  # Start very close to lowest data
                            'max': max(y_max, y_min + 10)  # Reasonable max
                        }
                    }
                },
                'interaction': {
                    'intersect': False,
                    'mode': 'index'
                }
            }
        }
        
        return config
    
    def _create_integration_area(self, time_points: List[float], intensity_points: List[float], 
                               int_start: float, int_end: float, ion, x_min: float, x_max: float, parent_lipid=None, ion_idx=0) -> Optional[Dict]:
        """
        Create integration area dataset for an annotated ion.
        """
        try:
            # Get annotation color
            color = self.annotation_colors.get(ion.annotation_type, self.annotation_colors['Default'])
            
            # Find data points within integration window
            integration_data = []
            
            # Add starting point at baseline
            integration_data.append({'x': int_start, 'y': 0})
            
            # Add actual data points within integration window
            for i, time in enumerate(time_points):
                if int_start <= time <= int_end:
                    integration_data.append({'x': time, 'y': intensity_points[i]})
            
            # Add ending point at baseline
            integration_data.append({'x': int_end, 'y': 0})
            
            if len(integration_data) < 3:  # Need at least start, some data, end
                return None
            
            # Create VERY light fill color (updated colors for user request)
            if color == '#40E0D0':  # Turquoise/cyan
                light_fill = "rgba(64, 224, 208, 0.12)"  # Very light turquoise
            elif color == '#1f77b4':  # Blue (Current lipid) 
                light_fill = "rgba(31, 119, 180, 0.12)"  # Very light blue
            elif color == '#ff4757':  # Light Red (isotope)
                light_fill = "rgba(255, 71, 87, 0.12)"   # Very light red
            elif color == '#2ed573':  # Light Green (Similar MRM)
                light_fill = "rgba(46, 213, 115, 0.12)"  # Very light green
            else:
                light_fill = "rgba(64, 224, 208, 0.12)"  # Default very light turquoise
            
            return {
                'label': f"{ion.ion_lipid_name}_area",  # UNIQUE label for each integration area
                'data': integration_data,
                'borderColor': color,
                'backgroundColor': light_fill,  # VERY light fill
                'borderWidth': 0.5,  # Thinner border
                'fill': True,
                'pointRadius': 0,
                'pointHoverRadius': 3,  # Enable hover detection for integration areas
                'pointHoverBorderWidth': 2,
                'order': 1,  # Draw on top of main line
                # Store INDIVIDUAL lipid info for THIS SPECIFIC integration area only
                'lipid_info': {
                    'lipid_name': ion.ion_lipid_name,
                    'lipid_class': parent_lipid.lipid_class.class_name if parent_lipid and parent_lipid.lipid_class else 'Unknown',
                    'retention_time': f"{float(ion.retention_time):.2f} minutes" if ion.retention_time else "N/A",
                    'integration_start': f"{float(ion.int_start):.2f} minutes" if ion.int_start else "N/A", 
                    'integration_end': f"{float(ion.int_end):.2f} minutes" if ion.int_end else "N/A",
                    'precursor_mass': f"{ion.precursor_ion} m/z" if ion.precursor_ion else "N/A",
                    'product_mass': f"{ion.product_ion} m/z" if ion.product_ion else "N/A",
                    'annotation': ion.annotation_type or "Similar MRM"
                },
                # Store the integration time range for precise hover detection
                'integration_range': {
                    'start': float(ion.int_start),
                    'end': float(ion.int_end)
                }
            }
            
        except Exception as e:
            print(f"Warning: Could not create integration area for {ion.ion_lipid_name}: {e}")
            return None
    
    def _create_annotation_point(self, time_points: List[float], intensity_points: List[float], ion) -> Optional[Dict]:
        """
        Create annotation point at peak maximum for hover information.
        """
        try:
            # Find intensity at retention time
            rt = float(ion.retention_time)
            closest_idx = min(range(len(time_points)), key=lambda i: abs(time_points[i] - rt))
            peak_intensity = intensity_points[closest_idx]
            
            color = self.annotation_colors.get(ion.annotation_type, self.annotation_colors['Default'])
            
            return {
                'label': f"{ion.ion_lipid_name} Peak",
                'data': [{'x': rt, 'y': peak_intensity}],
                'borderColor': color,
                'backgroundColor': color,
                'borderWidth': 2,
                'pointRadius': 4,
                'pointHoverRadius': 6,
                'showLine': False,  # Only show point, not line
                'annotation_info': f"{ion.annotation_type}, {ion.precursor_ion} → {ion.product_ion} m/z"
            }
            
        except Exception as e:
            print(f"Warning: Could not create annotation point for {ion.ion_lipid_name}: {e}")
            return None
    
    def _create_integration_boundary_lines(self, int_start: float, int_end: float, y_max: float, ion=None, ion_idx=0) -> List[Dict]:
        """
        Create vertical dashed lines at integration boundaries (like reference image).
        Returns two datasets: one for start line, one for end line.
        """
        try:
            boundary_lines = []
            
            # Integration start line (vertical dashed) - invisible to hover
            start_line = {
                'label': f'_boundary_line_start_{ion_idx}',  # Unique boundary line labels
                'data': [
                    {'x': int_start, 'y': 0},
                    {'x': int_start, 'y': y_max}
                ],
                'borderColor': 'rgba(70, 130, 180, 0.9)',  # Darker blue for better visibility
                'backgroundColor': 'rgba(0, 0, 0, 0)',
                'borderWidth': 1,
                'borderDash': [5, 5],  # Dashed line
                'fill': False,
                'pointRadius': 0,
                'pointHoverRadius': 0,
                'showLine': True,
                'order': 0,  # Draw on top
                'skip_tooltip': True  # Skip in tooltip completely
            }
            
            # Integration end line (vertical dashed) - invisible to hover
            end_line = {
                'label': f'_boundary_line_end_{ion_idx}',  # Unique boundary line labels
                'data': [
                    {'x': int_end, 'y': 0},
                    {'x': int_end, 'y': y_max}
                ],
                'borderColor': 'rgba(70, 130, 180, 0.9)',  # Darker blue for better visibility
                'backgroundColor': 'rgba(0, 0, 0, 0)',
                'borderWidth': 1,
                'borderDash': [5, 5],  # Dashed line
                'fill': False,
                'pointRadius': 0,
                'pointHoverRadius': 0,
                'showLine': True,
                'order': 0,  # Draw on top  
                'skip_tooltip': True  # Skip in tooltip completely
            }
            
            boundary_lines.extend([start_line, end_line])
            return boundary_lines
            
        except Exception as e:
            print(f"Warning: Could not create integration boundary lines: {e}")
            return []
    
    def _format_ion_data(self, ion) -> Dict[str, Any]:
        """Format annotated ion data for template use."""
        return {
            'ion_id': ion.ion_id,
            'lipid_name': ion.ion_lipid_name,
            'annotation_type': ion.annotation_type or 'Similar MRM',
            'retention_time': round(float(ion.retention_time), 2) if ion.retention_time else 'N/A',
            'precursor_ion': ion.precursor_ion or 'N/A',
            'product_ion': ion.product_ion or 'N/A',
            'integration_start': round(float(ion.int_start), 2) if ion.int_start else 'N/A',
            'integration_end': round(float(ion.int_end), 2) if ion.int_end else 'N/A',
            'collision_energy': ion.collision_energy or 'N/A',
            'is_main': ion.is_main_lipid,
            'color': self.annotation_colors.get(ion.annotation_type, self.annotation_colors['Default'])
        }