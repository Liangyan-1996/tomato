import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QSpinBox,
                              QComboBox, QPushButton, QVBoxLayout, QHBoxLayout,
                              QWidget)
from PyQt5.QtCore import QTimer
from datetime import datetime, timedelta
from timer_logic import FocusSessionManager
from database import FocusDatabase

class FocusTimerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)

    def init_ui(self):
        self.setWindowTitle('专注时钟')
        self.setGeometry(300, 300, 800, 600)
        
        # 创建核心组件
        self.time_label = QLabel('00:00', self)
        self.time_label.setStyleSheet('font-size: 48px;')
        
        # 设置面板
        self.total_time = QSpinBox(self)
        self.total_time.setRange(15, 240)
        self.total_time.setValue(60)
        
        self.work_duration = QSpinBox(self)
        self.work_duration.setRange(25, 40)
        self.work_duration.setValue(25)
        
        self.break_duration = QSpinBox(self)
        self.break_duration.setRange(1, 15)
        self.break_duration.setValue(5)
        
        # 声音选择
        self.sound_combo = QComboBox(self)
        self.sound_combo.addItems(['无', '雨声', '森林', '白噪声'])
        
        # 控制按钮
        self.start_btn = QPushButton('开始专注', self)
        self.start_btn.clicked.connect(self.start_session)
        
        self.pause_btn = QPushButton('暂停', self)
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)
        
        self.restart_btn = QPushButton('重启', self)
        self.restart_btn.clicked.connect(self.restart_session)
        self.restart_btn.setEnabled(False)
        
        self.abort_btn = QPushButton('中止', self)
        self.abort_btn.clicked.connect(self.abort_session)
        
        # 音频播放
        from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
        from PyQt5.QtCore import QUrl
        self.media_player = QMediaPlayer()
        
        # 统计面板
        self.today_stats = QLabel('今日专注: 0 小时', self)
        self.weekly_stats = QLabel('最近五日统计加载中...', self)
        
        # 布局设置
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.time_label)
        
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel('总时长(分钟):'))
        settings_layout.addWidget(self.total_time)
        settings_layout.addStretch(1)
        settings_layout.addWidget(QLabel('工作/休息时长:'))
        settings_layout.addWidget(self.work_duration)
        settings_layout.addWidget(QLabel('→'))
        settings_layout.addWidget(self.break_duration)
        
        main_layout.addLayout(settings_layout)
        sound_layout = QHBoxLayout()
        sound_layout.addWidget(QLabel('白噪声选择:'))
        sound_layout.addWidget(self.sound_combo, 1)
        main_layout.addLayout(sound_layout)
        main_layout.addWidget(self.start_btn)
        main_layout.addWidget(self.pause_btn)
        main_layout.addWidget(self.restart_btn)
        main_layout.addWidget(self.abort_btn)
        main_layout.addWidget(self.today_stats)
        main_layout.addWidget(self.weekly_stats)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # 初始化模块
        self.timer_manager = FocusSessionManager()
        self.database = FocusDatabase()
        self.update_stats()
        
    def start_session(self):
        self.media_player.stop()
        if self.sound_combo.currentText() != '无':
            sound_file = f'sounds/{self.sound_combo.currentText()}.mp3'
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_file)))
            self.media_player.play()
        total = self.total_time.value()
        work = self.work_duration.value()
        break_dur = self.break_duration.value()

        self.timer_manager.create_sessions(total, work, break_dur)
        self.timer.start(1000)
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)  # 新增启用暂停按钮

    def update_time(self):
        if hasattr(self, 'paused_remaining') and self.timer.isActive() == False:
            return

        now = datetime.now()
        session = self.timer_manager.get_current_session()
        
        if session:
            remaining = (session['end'] - now).total_seconds()
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            self.time_label.setText(f"{mins:02d}:{secs:02d}")
        else:
            self.timer.stop()
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)  # 禁用暂停按钮
            if self.timer_manager.sessions:
                last_session = self.timer_manager.sessions[-1]
                self.database.add_session(last_session['start'], last_session['end'], 'work')
                self.update_stats()

    def update_stats(self):
        stats = self.database.get_daily_stats()
        today = datetime.today().date().isoformat()
        today_hours = stats.get(today, 0)
        
        self.today_stats.setText(f'今日专注: {today_hours:.1f} 小时')
        weekly = [f'{k[-5:]}: {v:.1f}h' for k,v in sorted(stats.items())]
        self.weekly_stats.setText('最近五日:\n' + '\n'.join(weekly))

    def abort_session(self):
        # 完全停止计时器和清理所有状态
        self.timer.stop()
        self.timer_manager.sessions = []
        self.timer_manager.current_session = None
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setText('暂停')  # 重置暂停按钮文本
        self.media_player.stop()
        self.time_label.setText('00:00')
        if hasattr(self, 'paused_remaining'):
            del self.paused_remaining

    def toggle_pause(self):
        if not self.timer_manager.current_session:
            return
            
        if self.timer.isActive():
            # 计算剩余时间并停止计时器
            self.paused_remaining = (self.timer_manager.current_session['end'] - datetime.now()).total_seconds()
            self.timer.stop()
            self.pause_btn.setText('继续')
            self.restart_btn.setEnabled(True)
            self.start_btn.setEnabled(False)
            # 保存暂停时的时间显示
            mins = int(self.paused_remaining // 60)
            secs = int(self.paused_remaining % 60)
            self.time_label.setText(f"{mins:02d}:{secs:02d}")
        else:
            if hasattr(self, 'paused_remaining') and self.paused_remaining > 0:
                # 更新会话结束时间并重新启动计时器
                self.timer_manager.current_session['end'] = datetime.now() + timedelta(seconds=self.paused_remaining)
                self.timer.start(1000)
                self.pause_btn.setText('暂停')
                self.restart_btn.setEnabled(False)
                self.start_btn.setEnabled(False)

    def restart_session(self):
        if hasattr(self, 'paused_remaining') and self.paused_remaining > 0:
            self.timer_manager.current_session['end'] = datetime.now() + timedelta(seconds=self.paused_remaining)
            self.timer.start(1000)
            self.pause_btn.setText('暂停')
            self.pause_btn.setEnabled(True)
            self.restart_btn.setEnabled(False)
            self.start_btn.setEnabled(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FocusTimerApp()
    window.show()
    sys.exit(app.exec_())