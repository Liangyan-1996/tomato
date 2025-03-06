from datetime import datetime, timedelta

class FocusSessionManager:
    def __init__(self):
        self.sessions = []
        self.current_session = None

    def create_sessions(self, total_minutes, work_duration=25, break_duration=5):
        session_count = total_minutes // (work_duration + break_duration)
        remaining = total_minutes % (work_duration + break_duration)
        
        start_time = datetime.now()
        for _ in range(session_count):
            self.sessions.append({
                'type': 'work',
                'start': start_time,
                'end': start_time + timedelta(minutes=work_duration)
            })
            start_time += timedelta(minutes=work_duration)
            
            self.sessions.append({
                'type': 'break',
                'start': start_time,
                'end': start_time + timedelta(minutes=break_duration)
            })
            start_time += timedelta(minutes=break_duration)
        
        if remaining > 0:
            self.sessions.append({
                'type': 'work',
                'start': start_time,
                'end': start_time + timedelta(minutes=remaining)
            })

    def get_current_session(self):
        now = datetime.now()
        for session in self.sessions:
            if session['start'] <= now < session['end']:
                return session
        return None