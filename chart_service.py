"""
Metabolomics Chart Generation Service
Integrated with draw_both_charts_combined.py logic
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

# Import models
from models import db, MainLipid, AnnotatedIon

class MetabolomicsChartGenerator:
    """
    Chart generation service for metabolomics data visualization.
    Based on draw_both_charts_combined.py with Flask integration.
    """
    
    def __init__(self):
        self.color_mapping = {
            'Current lipid': '#1f77b4',      # Blue
            '+2 isotope': '#ff7f0e',         # Orange  
            'Similar MRM': '#d62728',        # Red
            'Default': '#2ca02c'             # Green
        }
        
        # Style configuration
        plt.style.use('default')
        self.figure_size = (15, 10)
        self.dpi = 100
    
    def generate_charts(self, lipid_id: int, selected_ion_ids: List[int], 
                       rt_window: float = 0.6, chart_type: str = 'dual') -> Dict:
        """
        Generate charts for a lipid with selected annotated ions.
        
        Args:
            lipid_id: Main lipid ID
            selected_ion_ids: List of annotated ion IDs to include
            rt_window: RT window for focused chart (default 0.6 min)
            chart_type: 'dual', 'focused', or 'overview'
            
        Returns:
            Dict with chart data and metadata
        """
        
        # Get lipid and ions data
        main_lipid = MainLipid.query.get_or_404(lipid_id)
        selected_ions = AnnotatedIon.query.filter(AnnotatedIon.ion_id.in_(selected_ion_ids)).all()
        
        if not selected_ions:
            raise ValueError("No valid annotated ions selected")
        
        # Prepare data for charting
        chart_data = self._prepare_chart_data(main_lipid, selected_ions)
        
        # Generate charts based on type
        if chart_type == 'dual':
            return self._generate_dual_charts(chart_data, rt_window)
        elif chart_type == 'focused':
            return self._generate_focused_chart(chart_data, rt_window)
        elif chart_type == 'overview':
            return self._generate_overview_chart(chart_data)
        else:
            raise ValueError(f"Invalid chart_type: {chart_type}")
    
    def _prepare_chart_data(self, main_lipid: MainLipid, selected_ions: List[AnnotatedIon]) -> Dict:
        """Prepare data structure for chart generation."""
        
        # Get XIC data from main lipid
        xic_data = main_lipid.xic_data if main_lipid.xic_data else []
        
        if not xic_data:
            raise ValueError(f"No XIC data available for {main_lipid.lipid_name}")
        
        # Parse XIC data
        time_points = []
        intensity_points = []
        
        for point in xic_data:
            if isinstance(point, dict) and 'time' in point and 'intensity' in point:
                time_points.append(float(point['time']))
                intensity_points.append(float(point['intensity']))
        
        if not time_points:
            raise ValueError("Invalid XIC data format")
        
        chart_data = {
            'main_lipid': {
                'name': main_lipid.lipid_name,
                'retention_time': main_lipid.retention_time,
                'class': main_lipid.lipid_class.class_name if main_lipid.lipid_class else 'Unknown'
            },
            'xic_data': {
                'time': time_points,
                'intensity': intensity_points
            },
            'annotated_ions': []
        }
        
        # Add ion information
        for ion in selected_ions:
            ion_data = {
                'name': ion.ion_lipid_name,
                'retention_time': ion.retention_time,
                'annotation_type': ion.annotation_type or 'Default',
                'is_main': ion.is_main_lipid,
                'color': self._get_ion_color(ion.annotation_type)
            }
            chart_data['annotated_ions'].append(ion_data)
        
        return chart_data
    
    def _get_ion_color(self, annotation_type: str) -> str:
        """Get color for ion based on annotation type."""
        return self.color_mapping.get(annotation_type, self.color_mapping['Default'])
    
    def _generate_dual_charts(self, chart_data: Dict, rt_window: float) -> Dict:
        """Generate dual chart view (focused + overview)."""
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=self.figure_size, dpi=self.dpi)
        
        time_data = np.array(chart_data['xic_data']['time'])
        intensity_data = np.array(chart_data['xic_data']['intensity'])
        main_rt = chart_data['main_lipid']['retention_time']
        
        # Chart 1: Focused view (RT ± window)
        if main_rt:
            focused_mask = (time_data >= main_rt - rt_window) & (time_data <= main_rt + rt_window)
            focused_time = time_data[focused_mask]
            focused_intensity = intensity_data[focused_mask]
        else:
            focused_time = time_data
            focused_intensity = intensity_data
        
        ax1.plot(focused_time, focused_intensity, 'b-', linewidth=2, label='XIC')
        ax1.set_title(f'Focused View: {chart_data["main_lipid"]["name"]} (RT ± {rt_window} min)', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlabel('Retention Time (min)', fontsize=12)
        ax1.set_ylabel('Intensity', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # Add ion markers to focused chart
        for ion in chart_data['annotated_ions']:
            if ion['retention_time'] and main_rt:
                if abs(ion['retention_time'] - main_rt) <= rt_window:
                    ax1.axvline(x=ion['retention_time'], color=ion['color'], 
                              linestyle='--', alpha=0.7, linewidth=2)
                    ax1.text(ion['retention_time'], max(focused_intensity) * 0.9, 
                           ion['name'], rotation=90, fontsize=9, 
                           verticalalignment='top', color=ion['color'])
        
        # Chart 2: Overview (full range with all ions)
        ax2.plot(time_data, intensity_data, 'b-', linewidth=1.5, alpha=0.7, label='XIC')
        ax2.set_title(f'Overview: All Annotated Ions (0-16 min)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Retention Time (min)', fontsize=12)
        ax2.set_ylabel('Intensity', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, 16)
        
        # Add all ion markers to overview
        for ion in chart_data['annotated_ions']:
            if ion['retention_time']:
                ax2.axvline(x=ion['retention_time'], color=ion['color'], 
                          linestyle='--', alpha=0.8, linewidth=2)
                ax2.text(ion['retention_time'], max(intensity_data) * 0.95, 
                       ion['annotation_type'], rotation=45, fontsize=8, 
                       verticalalignment='top', color=ion['color'])
        
        # Create legend for overview chart
        legend_elements = []
        used_types = set()
        for ion in chart_data['annotated_ions']:
            if ion['annotation_type'] not in used_types:
                legend_elements.append(plt.Line2D([0], [0], color=ion['color'], 
                                                lw=2, label=ion['annotation_type']))
                used_types.add(ion['annotation_type'])
        
        ax2.legend(handles=legend_elements, loc='upper right', fontsize=10)
        
        plt.tight_layout()
        
        # Convert to base64
        chart_image = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart_type': 'dual',
            'chart_image': chart_image,
            'metadata': {
                'main_lipid': chart_data['main_lipid']['name'],
                'rt_window': rt_window,
                'ions_count': len(chart_data['annotated_ions']),
                'generation_time': datetime.now().isoformat()
            }
        }
    
    def _generate_focused_chart(self, chart_data: Dict, rt_window: float) -> Dict:
        """Generate focused chart only."""
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 6), dpi=self.dpi)
        
        time_data = np.array(chart_data['xic_data']['time'])
        intensity_data = np.array(chart_data['xic_data']['intensity'])
        main_rt = chart_data['main_lipid']['retention_time']
        
        # Apply RT window filter
        if main_rt:
            focused_mask = (time_data >= main_rt - rt_window) & (time_data <= main_rt + rt_window)
            focused_time = time_data[focused_mask]
            focused_intensity = intensity_data[focused_mask]
        else:
            focused_time = time_data
            focused_intensity = intensity_data
        
        ax.plot(focused_time, focused_intensity, 'b-', linewidth=2, label='XIC')
        ax.set_title(f'Focused View: {chart_data["main_lipid"]["name"]} (RT ± {rt_window} min)', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Retention Time (min)', fontsize=12)
        ax.set_ylabel('Intensity', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add ion markers
        for ion in chart_data['annotated_ions']:
            if ion['retention_time'] and main_rt:
                if abs(ion['retention_time'] - main_rt) <= rt_window:
                    ax.axvline(x=ion['retention_time'], color=ion['color'], 
                             linestyle='--', alpha=0.7, linewidth=2, label=ion['name'])
        
        ax.legend(fontsize=10)
        plt.tight_layout()
        
        chart_image = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart_type': 'focused',
            'chart_image': chart_image,
            'metadata': {
                'main_lipid': chart_data['main_lipid']['name'],
                'rt_window': rt_window,
                'generation_time': datetime.now().isoformat()
            }
        }
    
    def _generate_overview_chart(self, chart_data: Dict) -> Dict:
        """Generate overview chart only."""
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 6), dpi=self.dpi)
        
        time_data = np.array(chart_data['xic_data']['time'])
        intensity_data = np.array(chart_data['xic_data']['intensity'])
        
        ax.plot(time_data, intensity_data, 'b-', linewidth=1.5, alpha=0.7, label='XIC')
        ax.set_title(f'Overview: {chart_data["main_lipid"]["name"]} - All Annotated Ions', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Retention Time (min)', fontsize=12)
        ax.set_ylabel('Intensity', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 16)
        
        # Add ion markers
        for ion in chart_data['annotated_ions']:
            if ion['retention_time']:
                ax.axvline(x=ion['retention_time'], color=ion['color'], 
                          linestyle='--', alpha=0.8, linewidth=2)
                ax.text(ion['retention_time'], max(intensity_data) * 0.95, 
                       ion['annotation_type'], rotation=45, fontsize=9, 
                       verticalalignment='top', color=ion['color'])
        
        # Create legend
        legend_elements = []
        used_types = set()
        for ion in chart_data['annotated_ions']:
            if ion['annotation_type'] not in used_types:
                legend_elements.append(plt.Line2D([0], [0], color=ion['color'], 
                                                lw=2, label=ion['annotation_type']))
                used_types.add(ion['annotation_type'])
        
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
        plt.tight_layout()
        
        chart_image = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            'chart_type': 'overview',
            'chart_image': chart_image,
            'metadata': {
                'main_lipid': chart_data['main_lipid']['name'],
                'ions_count': len(chart_data['annotated_ions']),
                'generation_time': datetime.now().isoformat()
            }
        }
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string for HTML embedding."""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        buffer.close()
        return f"data:image/png;base64,{image_base64}"
    
    def get_chart_data_json(self, lipid_id: int, selected_ion_ids: List[int], 
                           rt_window: float = 0.6) -> Dict:
        """Get chart data in JSON format for API/AJAX requests."""
        
        main_lipid = MainLipid.query.get_or_404(lipid_id)
        selected_ions = AnnotatedIon.query.filter(AnnotatedIon.ion_id.in_(selected_ion_ids)).all()
        
        chart_data = self._prepare_chart_data(main_lipid, selected_ions)
        
        # Add processing for client-side charting (e.g., Chart.js, D3.js)
        time_data = chart_data['xic_data']['time']
        intensity_data = chart_data['xic_data']['intensity']
        main_rt = chart_data['main_lipid']['retention_time']
        
        # Focused data
        focused_data = []
        if main_rt:
            for i, (t, intensity) in enumerate(zip(time_data, intensity_data)):
                if abs(t - main_rt) <= rt_window:
                    focused_data.append({'x': t, 'y': intensity})
        
        # Full data
        full_data = [{'x': t, 'y': intensity} for t, intensity in zip(time_data, intensity_data)]
        
        return {
            'main_lipid': chart_data['main_lipid'],
            'focused_data': focused_data,
            'full_data': full_data,
            'annotated_ions': chart_data['annotated_ions'],
            'rt_window': rt_window
        }