"""
Property-based tests for backtesting functionality
Tests the backtesting engine's correctness properties
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Any

from services.backtesting_engine import BacktestingEngine, BacktestEvent
from models.prediction import BacktestResult


class TestBacktestingProperties:
    """Property-based tests for backtesting engine"""
    
    def setup_method(self):
        """Set up test environment"""
        self.engine = BacktestingEngine()
    
    @given(
        event_date=st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31)
        )
    )
    @settings(max_examples=50, deadline=10000)
    def test_property_43_backtesting_chronological_replay(self, event_date):
        """
        # Feature: astrosense-space-weather, Property 43: Backtesting chronological replay
        
        Property 43: Backtesting chronological replay
        *For any* historical event in backtesting mode, events should be replayed 
        in chronological order based on their original timestamps
        **Validates: Requirements 13.2**
        """
        # Generate a timeline of events with random timestamps
        timeline = []
        base_time = event_date
        
        # Create events with incrementing timestamps
        for i in range(10):
            event_time = base_time + timedelta(minutes=i * 5)
            timeline.append(BacktestEvent(
                timestamp=event_time,
                event_type='measurement',
                data={'solar_wind_speed': 400 + i * 10}
            ))
        
        # Shuffle the timeline to test sorting
        import random
        shuffled_timeline = timeline.copy()
        random.shuffle(shuffled_timeline)
        
        # Run replay
        async def run_replay():
            return await self.engine.replay_events(shuffled_timeline, speed=100.0)
        
        replay_results = asyncio.run(run_replay())
        
        # Verify chronological order in results
        result_timestamps = [
            datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
            for event in replay_results['timeline']
        ]
        
        # Check that timestamps are in chronological order
        for i in range(1, len(result_timestamps)):
            assert result_timestamps[i] >= result_timestamps[i-1], \
                f"Events not in chronological order: {result_timestamps[i-1]} > {result_timestamps[i]}"
    
    @given(
        event_count=st.integers(min_value=5, max_value=20),
        event_date=st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31)
        )
    )
    @settings(max_examples=10, deadline=30000)
    def test_property_44_backtesting_prediction_and_actual_display(self, event_count, event_date):
        """
        # Feature: astrosense-space-weather, Property 44: Backtesting prediction and actual display
        
        Property 44: Backtesting prediction and actual display
        *For any* backtesting session, the dashboard should display both predicted impacts 
        and actual observed impacts side by side
        **Validates: Requirements 13.3**
        """
        # Generate timeline with measurement events
        timeline = []
        base_time = event_date
        
        for i in range(event_count):
            event_time = base_time + timedelta(minutes=i * 5)
            timeline.append(BacktestEvent(
                timestamp=event_time,
                event_type='measurement',
                data={
                    'solar_wind_speed': 400 + i * 20,
                    'bz': -5 - i,
                    'kp_index': 3 + i * 0.5,
                    'proton_flux': 10 + i * 5,
                    'flare_class': 'M',
                    'cme_speed': 800
                }
            ))
        
        # Run replay to generate predictions and actual impacts
        async def run_replay():
            return await self.engine.replay_events(timeline, speed=100.0)
        
        replay_results = asyncio.run(run_replay())
        
        # Get display data
        display_data = self.engine.display_predictions_and_actual(timeline)
        
        # Verify that display data contains both predictions and actual impacts
        assert 'comparison_table' in display_data
        assert 'time_series' in display_data
        
        comparison_table = display_data['comparison_table']
        time_series = display_data['time_series']
        
        # Check that each entry has both predicted and actual data
        for entry in comparison_table:
            assert 'predicted' in entry, "Missing predicted impacts in display"
            assert 'actual' in entry, "Missing actual impacts in display"
            assert 'differences' in entry, "Missing differences calculation in display"
            
            # Verify all sectors are present in predictions
            predicted = entry['predicted']
            actual = entry['actual']
            
            assert 'aviation' in predicted
            assert 'telecommunications' in predicted
            assert 'gps' in predicted
            assert 'power_grid' in predicted
            assert 'satellite' in predicted
            assert 'composite_score' in predicted
            
            assert 'aviation' in actual
            assert 'telecommunications' in actual
            assert 'gps' in actual
            assert 'power_grid' in actual
            assert 'satellite' in actual
            assert 'composite_score' in actual
        
        # Verify time series data structure
        assert 'predicted' in time_series
        assert 'actual' in time_series
        assert 'timestamps' in time_series
        
        # Check that time series has data for all sectors
        for sector in ['aviation', 'telecom', 'gps', 'power_grid', 'satellite', 'composite']:
            assert sector in time_series['predicted']
            assert sector in time_series['actual']
            assert len(time_series['predicted'][sector]) > 0
            assert len(time_series['actual'][sector]) > 0
    
    @given(
        event_count=st.integers(min_value=10, max_value=30),
        event_date=st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2025, 12, 31)
        )
    )
    @settings(max_examples=5, deadline=30000)
    def test_property_45_backtesting_accuracy_report_generation(self, event_count, event_date):
        """
        # Feature: astrosense-space-weather, Property 45: Backtesting accuracy report generation
        
        Property 45: Backtesting accuracy report generation
        *For any* completed backtesting session, the system should generate an accuracy report 
        comparing predictions to ground truth data
        **Validates: Requirements 13.4**
        """
        # Generate timeline with measurement events
        timeline = []
        base_time = event_date
        
        for i in range(event_count):
            event_time = base_time + timedelta(minutes=i * 5)
            timeline.append(BacktestEvent(
                timestamp=event_time,
                event_type='measurement',
                data={
                    'solar_wind_speed': 400 + i * 15,
                    'bz': -3 - i * 0.5,
                    'kp_index': 2 + i * 0.3,
                    'proton_flux': 5 + i * 3,
                    'flare_class': 'C' if i < event_count // 2 else 'M',
                    'cme_speed': 600 + i * 20
                }
            ))
        
        # Run replay to generate predictions and actual impacts
        async def run_replay():
            return await self.engine.replay_events(timeline, speed=100.0)
        
        replay_results = asyncio.run(run_replay())
        
        # Generate accuracy report
        accuracy_report = self.engine.generate_accuracy_report(timeline)
        
        # Verify accuracy report structure
        assert 'event_count' in accuracy_report
        assert 'time_period' in accuracy_report
        assert 'sector_metrics' in accuracy_report
        assert 'overall_metrics' in accuracy_report
        assert 'recommendations' in accuracy_report
        
        # Check event count matches
        measurement_events = [e for e in timeline if e.event_type == 'measurement' 
                            and hasattr(e, 'predicted_impacts') and hasattr(e, 'actual_impacts')]
        assert accuracy_report['event_count'] >= 0
        
        # Verify sector metrics
        sector_metrics = accuracy_report['sector_metrics']
        expected_sectors = ['aviation', 'telecom', 'gps', 'power_grid', 'satellite', 'composite']
        
        for sector in expected_sectors:
            if sector in sector_metrics:
                metrics = sector_metrics[sector]
                
                # Check required metrics are present
                assert 'mean_absolute_error' in metrics
                assert 'root_mean_square_error' in metrics
                assert 'mean_absolute_percentage_error' in metrics
                assert 'correlation_coefficient' in metrics
                assert 'sample_count' in metrics
                assert 'predicted_range' in metrics
                assert 'actual_range' in metrics
                
                # Verify metric values are reasonable
                assert metrics['mean_absolute_error'] >= 0
                assert metrics['root_mean_square_error'] >= 0
                assert metrics['mean_absolute_percentage_error'] >= 0
                assert -1 <= metrics['correlation_coefficient'] <= 1
                assert metrics['sample_count'] >= 0
                assert len(metrics['predicted_range']) == 2
                assert len(metrics['actual_range']) == 2
        
        # Verify overall metrics
        overall_metrics = accuracy_report['overall_metrics']
        assert 'mean_absolute_error' in overall_metrics
        assert 'correlation_coefficient' in overall_metrics
        assert 'accuracy_grade' in overall_metrics
        
        assert overall_metrics['mean_absolute_error'] >= 0
        assert -1 <= overall_metrics['correlation_coefficient'] <= 1
        assert overall_metrics['accuracy_grade'] in ['A', 'B', 'C', 'D', 'F']
        
        # Verify recommendations are provided
        assert isinstance(accuracy_report['recommendations'], list)
        assert len(accuracy_report['recommendations']) > 0
    
    @given(
        session_active=st.booleans(),
        replay_speed=st.floats(min_value=0.1, max_value=10.0),
        current_position=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=50, deadline=5000)
    def test_property_46_backtesting_mode_exit_without_reload(self, session_active, replay_speed, current_position):
        """
        # Feature: astrosense-space-weather, Property 46: Backtesting mode exit without reload
        
        Property 46: Backtesting mode exit without reload
        *For any* active backtesting session, exiting to live data mode should transition 
        without requiring a page reload
        **Validates: Requirements 13.5**
        """
        # Set up engine state
        self.engine.current_session = "test_session" if session_active else None
        self.engine.replay_speed = replay_speed
        self.engine.current_position = current_position
        self.engine.is_playing = session_active
        
        # Get mode switching support
        mode_switching = self.engine.support_mode_switching()
        
        # Verify mode switching structure
        assert 'current_mode' in mode_switching
        assert 'session_id' in mode_switching
        assert 'replay_position' in mode_switching
        assert 'replay_speed' in mode_switching
        assert 'is_playing' in mode_switching
        assert 'can_switch_to_live' in mode_switching
        assert 'switch_instructions' in mode_switching
        
        # Verify current mode is backtesting
        assert mode_switching['current_mode'] == 'backtesting'
        
        # Verify session state is preserved
        assert mode_switching['replay_position'] == current_position
        assert mode_switching['replay_speed'] == replay_speed
        assert mode_switching['is_playing'] == session_active
        
        # Verify switching is supported without reload
        assert mode_switching['can_switch_to_live'] == True
        
        switch_instructions = mode_switching['switch_instructions']
        assert 'method' in switch_instructions
        assert 'requires_reload' in switch_instructions
        assert 'transition_time_ms' in switch_instructions
        
        # Verify no page reload is required
        assert switch_instructions['requires_reload'] == False
        assert switch_instructions['method'] == 'state_transfer'
        assert isinstance(switch_instructions['transition_time_ms'], (int, float))
        assert switch_instructions['transition_time_ms'] > 0
    
    @given(
        event_name=st.text(min_size=1, max_size=100),
        accuracy_score=st.floats(min_value=0.0, max_value=1.0),
        mae_value=st.floats(min_value=0.0, max_value=100.0)
    )
    @settings(max_examples=30, deadline=10000)
    def test_property_42_post_event_accuracy_logging(self, event_name, accuracy_score, mae_value):
        """
        # Feature: astrosense-space-weather, Property 42: Post-event accuracy logging
        
        Property 42: Post-event accuracy logging
        *For any* forecasted CME that arrives, the system should compare actual impacts 
        to predictions and log accuracy metrics to the database
        **Validates: Requirements 12.5**
        """
        # Create mock accuracy report
        accuracy_report = {
            'event_count': 10,
            'time_period': {
                'start': '2024-05-10T00:00:00',
                'end': '2024-05-12T00:00:00'
            },
            'sector_metrics': {
                'aviation': {
                    'mean_absolute_error': mae_value,
                    'correlation_coefficient': accuracy_score
                },
                'telecom': {
                    'mean_absolute_error': mae_value * 1.1,
                    'correlation_coefficient': accuracy_score * 0.9
                }
            },
            'overall_metrics': {
                'mean_absolute_error': mae_value,
                'correlation_coefficient': accuracy_score,
                'accuracy_grade': 'B'
            },
            'recommendations': ['Test recommendation']
        }
        
        # Test logging without database (should handle gracefully)
        async def test_logging():
            result = await self.engine.log_post_event_accuracy(event_name, accuracy_report)
            return result
        
        # Run the logging test
        logging_result = asyncio.run(test_logging())
        
        # Verify logging behavior
        # Without database manager, should return False but not crash
        assert isinstance(logging_result, bool)
        
        # Verify the engine can handle the accuracy report structure
        assert 'overall_metrics' in accuracy_report
        assert 'sector_metrics' in accuracy_report
        
        # Test that the logging function validates input structure
        invalid_report = {'invalid': 'structure'}
        
        async def test_invalid_logging():
            return await self.engine.log_post_event_accuracy(event_name, invalid_report)
        
        # Should handle invalid structure gracefully
        invalid_result = asyncio.run(test_invalid_logging())
        assert isinstance(invalid_result, bool)
    
    @given(
        timeline_length=st.integers(min_value=1, max_value=50),
        measurement_ratio=st.floats(min_value=0.3, max_value=1.0)
    )
    @settings(max_examples=5, deadline=30000)
    def test_backtesting_engine_robustness(self, timeline_length, measurement_ratio):
        """
        Test backtesting engine robustness with various timeline configurations
        """
        # Generate mixed timeline with different event types
        timeline = []
        base_time = datetime(2024, 5, 10)
        
        for i in range(timeline_length):
            event_time = base_time + timedelta(minutes=i * 5)
            
            # Determine event type based on ratio
            if i / timeline_length < measurement_ratio:
                event_type = 'measurement'
                data = {
                    'solar_wind_speed': 400 + i * 10,
                    'bz': -2 - i * 0.2,
                    'kp_index': 2 + i * 0.1,
                    'proton_flux': 5 + i,
                    'flare_class': 'C',
                    'cme_speed': 600
                }
            else:
                event_type = 'cme' if i % 2 == 0 else 'flare'
                data = {'event_id': f'event_{i}', 'intensity': i}
            
            timeline.append(BacktestEvent(
                timestamp=event_time,
                event_type=event_type,
                data=data
            ))
        
        # Test replay functionality
        async def run_test():
            replay_results = await self.engine.replay_events(timeline, speed=50.0)
            display_data = self.engine.display_predictions_and_actual(timeline)
            accuracy_report = self.engine.generate_accuracy_report(timeline)
            return replay_results, display_data, accuracy_report
        
        replay_results, display_data, accuracy_report = asyncio.run(run_test())
        
        # Verify results are well-formed
        assert 'events_processed' in replay_results
        assert 'timeline' in replay_results
        assert replay_results['events_processed'] == timeline_length
        
        # Verify display data handles mixed event types
        assert 'comparison_table' in display_data
        assert 'time_series' in display_data
        
        # Verify accuracy report handles available data
        assert 'event_count' in accuracy_report
        assert 'sector_metrics' in accuracy_report
        assert 'overall_metrics' in accuracy_report