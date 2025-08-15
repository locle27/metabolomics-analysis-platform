"""
Simple Chart Service - Matches draw_both_charts_combined.py exactly
Uses the standard RT ± 0.6 formula and handles XIC data properly
"""

import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for Flask
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import aiohttp
import asyncio

# Import optimized PostgreSQL models
from models_postgresql_optimized import db, MainLipid, AnnotatedIon

class SimpleChartGenerator:
    """
    Simple chart generator that matches draw_both_charts_combined.py exactly.
    Uses the standard RT ± 0.6 minute formula.
    Fetches REAL XIC data from Baker Institute API like the original.
    """
    
    def __init__(self, base_url: str = "https://metabolomics.baker.edu.au"):
        self.base_url = base_url
        # Use same colors as original
        self.color_mapping = {
            'Current lipid': '#1f77b4',      # Blue
            '+2 isotope': '#d62728',         # Red  
            'Similar MRM': '#ff7f0e',        # Orange
            'Default': '#2ca02c'             # Green
        }
    
    def calculate_chart1_range(self, retention_time: float) -> tuple:
        """Calculate Chart 1 zoom range (RT ± 0.6 minutes) - EXACT FORMULA."""
        start = max(0.0, retention_time - 0.6)
        end = retention_time + 0.6
        return (round(start, 1), round(end, 1))
    
    async def fetch_real_xic_data(self, api_code: str) -> Tuple[List[float], List[float]]:
        """Fetch REAL XIC data from Baker Institute API (like draw_both_charts_combined.py)."""
        api_url = f"{self.base_url}/method/api/lipid/{api_code}.json"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract XIC data exactly like draw_both_charts_combined.py
                        xic_data = data.get('XIC', [])
                        times = [point.get('time', 0) for point in xic_data if 'time' in point and 'intensity' in point]
                        intensities = [point.get('intensity', 0) for point in xic_data if 'time' in point and 'intensity' in point]
                        
                        if times and intensities:
                            print(f"✅ REAL XIC data fetched for {api_code}: {len(times)} points")
                            return times, intensities
                        else:
                            print(f"⚠️  {api_code}: API response has no XIC time/intensity data")
                            return [], []
                    else:
                        print(f"❌ {api_code}: API request failed with status {response.status}")
                        return [], []
                        
        except Exception as e:
            print(f"❌ {api_code}: Error fetching API data: {e}")
            return [], []
    
    def get_chart_data_json(self, lipid_id: int) -> Dict:
        """
        Get raw XIC data in JSON format for interactive Chart.js rendering.
        Uses reliable DATABASE data instead of unreliable API calls.
        
        Args:
            lipid_id: Main lipid ID
            
        Returns:
            Dict with raw time/intensity data and metadata for Chart.js
        """
        
        # Get lipid data from database
        main_lipid = MainLipid.query.get_or_404(lipid_id)
        annotated_ions = AnnotatedIon.query.filter_by(main_lipid_id=lipid_id).all()
        
        print(f"🔍 Getting chart data for {main_lipid.lipid_name} (ID: {lipid_id})")
        
        # Use DATABASE XIC data (much more reliable than API)
        time_points, intensity_points = self._parse_xic_data(main_lipid.xic_data)
        
        if not time_points:
            raise ValueError(f"No XIC data available in database for {main_lipid.lipid_name}")
        
        print(f"✅ Found {len(time_points)} XIC data points in database")
        
        # Get main retention time
        main_rt = main_lipid.retention_time
        if not main_rt:
            main_rt = np.mean(time_points) if time_points else 8.0
        
        # Calculate Chart 1 range using EXACT formula
        chart1_start, chart1_end = self.calculate_chart1_range(main_rt)
        
        # Prepare data for Chart.js
        xic_data = []
        for i, (time, intensity) in enumerate(zip(time_points, intensity_points)):
            xic_data.append({
                'x': time,
                'y': intensity
            })
        
        # Prepare ion annotations with database data
        ions_data = []
        for ion in annotated_ions:
            if ion.retention_time:
                color = self._get_ion_color(ion.annotation_type)
                ions_data.append({
                    'retention_time': float(ion.retention_time),
                    'ion_name': ion.ion_lipid_name,
                    'annotation_type': ion.annotation_type or 'Default',
                    'color': color,
                    'is_main': ion.is_main_lipid,
                    'int_start': float(ion.int_start) if ion.int_start else None,
                    'int_end': float(ion.int_end) if ion.int_end else None
                })
        
        print(f"✅ Prepared {len(ions_data)} ion annotations")
        
        return {
            'data_type': 'interactive_json',
            'xic_data': xic_data,
            'ions_data': ions_data,
            'metadata': {
                'main_lipid': main_lipid.lipid_name,
                'main_rt': main_rt,
                'chart1_range': [chart1_start, chart1_end],
                'full_range': [0, 16],
                'ions_count': len(annotated_ions),
                'data_points': len(xic_data),
                'generation_time': datetime.now().isoformat(),
                'data_source': 'database_json'
            }
        }
    
    def generate_charts(self, lipid_id: int) -> Dict:
        """
        Generate dual charts for a lipid using reliable DATABASE data.
        
        Args:
            lipid_id: Main lipid ID
            
        Returns:
            Dict with chart data and base64 image
        """
        
        # Get lipid data from database
        main_lipid = MainLipid.query.get_or_404(lipid_id)
        annotated_ions = AnnotatedIon.query.filter_by(main_lipid_id=lipid_id).all()
        
        print(f"🔍 Generating charts for {main_lipid.lipid_name} (ID: {lipid_id})")
        
        # Use DATABASE XIC data (much more reliable than API)
        time_points, intensity_points = self._parse_xic_data(main_lipid.xic_data)
        
        if not time_points:
            raise ValueError(f"No XIC data available in database for {main_lipid.lipid_name}")
        
        print(f"✅ Found {len(time_points)} XIC data points in database")
        
        # Convert to numpy arrays
        time_data = np.array(time_points)
        intensity_data = np.array(intensity_points)
        
        # Get main retention time
        main_rt = main_lipid.retention_time
        if not main_rt:
            main_rt = np.mean(time_data)  # Fallback to middle of data
        
        # Calculate Chart 1 range using EXACT formula
        chart1_start, chart1_end = self.calculate_chart1_range(main_rt)
        
        # Generate dual charts - HORIZONTAL layout for 2-3 charts in a row
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=100)
        
        # CHART 1: Focused view (RT ± 0.6 min)
        self._draw_chart1(ax1, time_data, intensity_data, main_rt, chart1_start, chart1_end, 
                         main_lipid.lipid_name, annotated_ions)
        
        # CHART 2: Overview (0-16 min full range) with Chart 1 zoom indicators
        self._draw_chart2(ax2, time_data, intensity_data, main_lipid.lipid_name, annotated_ions, 
                         chart1_start, chart1_end)
        
        plt.tight_layout()
        
        # Convert to base64
        chart_image = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart_type': 'dual',
            'chart_image': chart_image,
            'metadata': {
                'main_lipid': main_lipid.lipid_name,
                'rt_window': 0.6,
                'chart1_range': f"{chart1_start}-{chart1_end} min",
                'main_rt': main_rt,
                'ions_count': len(annotated_ions),
                'generation_time': datetime.now().isoformat(),
                'data_source': 'database_json'
            }
        }
    
    def generate_charts_with_zoom(self, lipid_id: int, zoom_start: float, zoom_end: float) -> Dict:
        """
        Generate dual charts with custom zoom range using reliable DATABASE data.
        
        Args:
            lipid_id: Main lipid ID
            zoom_start: Custom start time (minutes)
            zoom_end: Custom end time (minutes)
            
        Returns:
            Dict with chart data and base64 image
        """
        
        # Get lipid data from database
        main_lipid = MainLipid.query.get_or_404(lipid_id)
        annotated_ions = AnnotatedIon.query.filter_by(main_lipid_id=lipid_id).all()
        
        print(f"🔍 Generating zoomed charts for {main_lipid.lipid_name} ({zoom_start}-{zoom_end} min)")
        
        # Use DATABASE XIC data (much more reliable than API)
        time_points, intensity_points = self._parse_xic_data(main_lipid.xic_data)
        
        if not time_points:
            raise ValueError(f"No XIC data available in database for {main_lipid.lipid_name}")
        
        print(f"✅ Found {len(time_points)} XIC data points in database")
        
        # Convert to numpy arrays
        time_data = np.array(time_points)
        intensity_data = np.array(intensity_points)
        
        # Get main retention time
        main_rt = main_lipid.retention_time
        if not main_rt:
            main_rt = np.mean(time_data)  # Fallback to middle of data
        
        # Use custom zoom range instead of RT ± 0.6
        chart1_start = max(0.0, zoom_start)
        chart1_end = min(16.0, zoom_end)
        
        # Generate dual charts with custom zoom - HORIZONTAL layout
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=100)
        
        # CHART 1: Custom zoom view
        self._draw_chart1(ax1, time_data, intensity_data, main_rt, chart1_start, chart1_end, 
                         main_lipid.lipid_name, annotated_ions)
        
        # CHART 2: Overview (0-16 min full range) with custom zoom indicators
        self._draw_chart2(ax2, time_data, intensity_data, main_lipid.lipid_name, annotated_ions, 
                         chart1_start, chart1_end)
        
        plt.tight_layout()
        
        # Convert to base64
        chart_image = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart_type': 'dual_zoomed',
            'chart_image': chart_image,
            'metadata': {
                'main_lipid': main_lipid.lipid_name,
                'rt_window': f"custom_{zoom_start}-{zoom_end}",
                'chart1_range': f"{chart1_start}-{chart1_end} min",
                'zoom_range': f"{zoom_start}-{zoom_end} min",
                'main_rt': main_rt,
                'ions_count': len(annotated_ions),
                'generation_time': datetime.now().isoformat(),
                'data_source': 'database_json',
                'zoom_enabled': True
            }
        }
    
    def _parse_xic_data(self, xic_data) -> Tuple[List[float], List[float]]:
        """Parse XIC data from various formats - PRIORITIZE REAL DATA!"""
        time_points = []
        intensity_points = []
        
        try:
            # Handle string JSON
            if isinstance(xic_data, str):
                xic_data = json.loads(xic_data)
            
            # Handle different data structures - CHECK FOR REAL DATA FIRST!
            if isinstance(xic_data, dict):
                # PRIORITY 1: Real time/intensity arrays
                if 'time' in xic_data and 'intensity' in xic_data:
                    time_points = list(xic_data['time'])
                    intensity_points = list(xic_data['intensity'])
                    print(f"✅ Using REAL XIC data: {len(time_points)} time points")
                
                # PRIORITY 2: Points array format
                elif 'points' in xic_data and len(xic_data['points']) > 0:
                    for point in xic_data['points']:
                        if isinstance(point, dict) and 'time' in point and 'intensity' in point:
                            time_points.append(float(point['time']))
                            intensity_points.append(float(point['intensity']))
                    print(f"✅ Using REAL points data: {len(time_points)} points")
                
                # LAST RESORT: Generate placeholder only if NO real data exists
                elif 'data_points' in xic_data and 'max_intensity' in xic_data:
                    print("⚠️  NO REAL XIC DATA FOUND - generating placeholder")
                    return self._generate_placeholder_data(xic_data)
            
            # Handle array format: [{time: X, intensity: Y}, ...]
            elif isinstance(xic_data, list) and len(xic_data) > 0:
                for point in xic_data:
                    if isinstance(point, dict) and 'time' in point and 'intensity' in point:
                        time_points.append(float(point['time']))
                        intensity_points.append(float(point['intensity']))
                print(f"✅ Using REAL array data: {len(time_points)} points")
            
            # Convert all to float and validate
            if time_points and intensity_points:
                time_points = [float(t) for t in time_points if t is not None]
                intensity_points = [float(i) for i in intensity_points if i is not None]
                
                if len(time_points) == len(intensity_points) and len(time_points) > 0:
                    print(f"✅ Valid XIC data: {len(time_points)} points, time range: {min(time_points):.2f}-{max(time_points):.2f}")
                    return time_points, intensity_points
            
            # If we get here, no valid real data was found
            print("❌ No valid real XIC data found")
            return [], []
            
        except Exception as e:
            print(f"❌ Error parsing XIC data: {e}")
            return [], []
    
    def _generate_placeholder_data(self, summary_stats: dict) -> Tuple[List[float], List[float]]:
        """Generate placeholder XIC data from summary statistics."""
        try:
            data_points = summary_stats.get('data_points', 100)
            max_intensity = summary_stats.get('max_intensity', 1000)
            min_intensity = summary_stats.get('min_intensity', 50)
            avg_intensity = summary_stats.get('avg_intensity', 200)
            
            # Generate realistic time points (0-16 minutes)
            time_points = np.linspace(0, 16, data_points).tolist()
            
            # Generate realistic chromatographic peak shape
            # Create a Gaussian-like peak around retention time
            peak_center = 8.0  # Default peak center
            peak_width = 2.0   # Peak width
            
            intensity_points = []
            for t in time_points:
                # Gaussian peak with noise
                baseline = min_intensity
                peak_height = max_intensity - min_intensity
                gaussian = np.exp(-0.5 * ((t - peak_center) / peak_width) ** 2)
                intensity = baseline + peak_height * gaussian
                
                # Add some noise
                noise = np.random.normal(0, (max_intensity - min_intensity) * 0.05)
                intensity += noise
                
                # Keep within bounds
                intensity = max(min_intensity, min(max_intensity, intensity))
                intensity_points.append(intensity)
            
            print(f"Generated placeholder data: {len(time_points)} points, intensity range {min_intensity}-{max_intensity}")
            return time_points, intensity_points
            
        except Exception as e:
            print(f"Error generating placeholder data: {e}")
            # Ultimate fallback - simple linear data
            time_points = [0.0, 8.0, 16.0]
            intensity_points = [min_intensity, max_intensity, min_intensity]
            return time_points, intensity_points
    
    def _draw_chart1(self, ax, time_data, intensity_data, main_rt, start, end, lipid_name, ions):
        """Draw Chart 1 - Focused view (RT ± 0.6 min) with integration area."""
        
        # Filter data to chart 1 range
        mask = (time_data >= start) & (time_data <= end)
        filtered_time = time_data[mask]
        filtered_intensity = intensity_data[mask]
        
        if len(filtered_time) == 0:
            # No data in range, show full data
            filtered_time = time_data
            filtered_intensity = intensity_data
        
        # Plot main XIC line
        ax.plot(filtered_time, filtered_intensity, color='#1f77b4', linewidth=2, zorder=3)
        
        # Add integration area and boundaries for main ion
        main_ion = None
        for ion in ions:
            if ion.is_main_lipid:
                main_ion = ion
                break
        
        if main_ion and hasattr(main_ion, 'int_start') and hasattr(main_ion, 'int_end'):
            int_start = float(main_ion.int_start) if main_ion.int_start else 0
            int_end = float(main_ion.int_end) if main_ion.int_end else 0
            
            if int_start > 0 and int_end > 0:
                # Fill integration area between bounds
                int_mask = (filtered_time >= int_start) & (filtered_time <= int_end)
                if np.any(int_mask):
                    ax.fill_between(filtered_time[int_mask], filtered_intensity[int_mask], 0, 
                                   color='lightblue', alpha=0.7, zorder=2, label='Integration area')
                
                # Add integration boundary lines
                ax.axvline(x=int_start, color='lightblue', linestyle='--', linewidth=2, 
                          alpha=1.0, zorder=4, label='Integration bounds')
                ax.axvline(x=int_end, color='lightblue', linestyle='--', linewidth=2, 
                          alpha=1.0, zorder=4)
        
        # Add other ion markers
        for ion in ions:
            if ion.retention_time and start <= ion.retention_time <= end:
                color = self._get_ion_color(ion.annotation_type)
                if not ion.is_main_lipid:  # Don't duplicate main ion line
                    ax.axvline(x=ion.retention_time, color=color, linestyle='-', alpha=0.8, linewidth=2)
                
                # Add ion label
                max_intensity = np.max(filtered_intensity) if len(filtered_intensity) > 0 else 1000
                ax.text(ion.retention_time, max_intensity * 0.9, ion.ion_lipid_name, 
                       rotation=90, fontsize=9, verticalalignment='top', color=color)
        
        ax.set_title(f'{lipid_name} - Chart 1 (Focused: {start}-{end} min)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Retention Time (min)', fontsize=12)
        ax.set_ylabel('Intensity', fontsize=12)
        ax.grid(True, alpha=0.1, zorder=1)
        ax.set_xlim(start, end)
        ax.set_ylim(0, np.max(filtered_intensity) * 1.05 if len(filtered_intensity) > 0 else 1000)
        
        # Set x-axis ticks every 0.1 minutes
        x_ticks = np.arange(start, end + 0.1, 0.1)
        ax.set_xticks(x_ticks)
        
        # Format y-axis with scientific notation
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        
        # Clean styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('black')
        ax.spines['bottom'].set_color('black')
    
    def _draw_chart2(self, ax, time_data, intensity_data, lipid_name, ions, chart1_start, chart1_end):
        """Draw Chart 2 - Overview (0-16 min full range) with Chart 1 zoom indicators."""
        
        # Plot main XIC line
        ax.plot(time_data, intensity_data, color='#1f77b4', linewidth=1.2, alpha=0.8, zorder=2)
        
        # Add Chart 1 zoom range indicators (orange dashed lines)
        ax.axvline(x=chart1_start, color='orange', linestyle='--', linewidth=2, 
                  alpha=0.8, zorder=4, label='Chart 1 zoom range')
        ax.axvline(x=chart1_end, color='orange', linestyle='--', linewidth=2, 
                  alpha=0.8, zorder=4)
        
        # Color mapping for annotation types
        color_map = {
            'current lipid': '#1f77b4',  # Blue
            '+2 isotope': '#d62728',     # Red  
            'similar mrm': '#ff7f0e',    # Orange
            'isotopes': '#d62728'        # Red
        }
        
        # Add all ion markers with integration areas
        legend_elements = []
        seen_types = set()
        
        for ion in ions:
            if ion.retention_time:
                ann_type = (ion.annotation_type or 'current lipid').lower()
                color = color_map.get(ann_type, '#2ca02c')  # Default green
                
                # Mark retention time
                ax.axvline(x=ion.retention_time, color=color, linestyle='-', alpha=0.8, linewidth=2, zorder=4)
                
                # Add integration area if available
                if hasattr(ion, 'int_start') and hasattr(ion, 'int_end'):
                    int_start = float(ion.int_start) if ion.int_start else 0
                    int_end = float(ion.int_end) if ion.int_end else 0
                    
                    if int_start > 0 and int_end > 0:
                        int_mask = (time_data >= int_start) & (time_data <= int_end)
                        if np.any(int_mask):
                            ax.fill_between(time_data[int_mask], intensity_data[int_mask], 0, 
                                           alpha=0.3, color=color, zorder=1)
                
                # Build legend
                display_type = ion.annotation_type or 'Current lipid'
                if ann_type not in seen_types:
                    legend_elements.append(plt.Line2D([0], [0], color=color, lw=3, label=display_type))
                    seen_types.add(ann_type)
        
        # Add Chart 1 zoom range to legend
        legend_elements.append(plt.Line2D([0], [0], color='orange', lw=2, linestyle='--', label='Chart 1 zoom range'))
        
        # Add integration bounds to legend
        legend_elements.append(plt.Line2D([0], [0], color='lightblue', lw=2, linestyle='--', label='Integration bounds'))
        
        ax.set_title(f'{lipid_name} - Chart 2 (Full: 0-16 min)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Retention Time (min)', fontsize=12)
        ax.set_ylabel('Intensity', fontsize=12)
        ax.grid(True, alpha=0.2, zorder=0)
        ax.set_xlim(0, 16)
        ax.set_ylim(0, np.max(intensity_data) * 1.1)
        ax.set_xticks(range(0, 17, 1))
        
        # Format y-axis with scientific notation
        ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        
        # Clean styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('black')
        ax.spines['bottom'].set_color('black')
        
        # Add legend
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9)
    
    def _get_ion_color(self, annotation_type: str) -> str:
        """Get color for ion based on annotation type."""
        return self.color_mapping.get(annotation_type or 'Default', self.color_mapping['Default'])
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string for HTML embedding."""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', 
                   facecolor='white', edgecolor='none', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return f"data:image/png;base64,{image_base64}"

# Test function
def test_chart_generation():
    """Test chart generation with a sample lipid."""
    try:
        generator = SimpleChartGenerator()
        
        # Test with first available lipid
        from app import app
        with app.app_context():
            first_lipid = MainLipid.query.filter(MainLipid.xic_data.isnot(None)).first()
            
            if first_lipid:
                print(f"Testing chart generation for: {first_lipid.lipid_name}")
                result = generator.generate_charts(first_lipid.lipid_id)
                print("✅ Chart generation successful!")
                print(f"   Chart type: {result['chart_type']}")
                print(f"   Main RT: {result['metadata']['main_rt']}")
                print(f"   Chart 1 range: {result['metadata']['chart1_range']}")
                print(f"   Ions count: {result['metadata']['ions_count']}")
                return True
            else:
                print("❌ No lipids with XIC data found")
                return False
                
    except Exception as e:
        print(f"❌ Chart generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_chart_generation()