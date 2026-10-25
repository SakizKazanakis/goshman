"""GOSHMAN Windows desktop shell. Real file operations and async Blender subprocess."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QProcess, QThreadPool, QRunnable, QObject, Signal, Slot
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QLabel, QLineEdit, QPushButton, QSpinBox,
    QComboBox, QPlainTextEdit, QTabWidget, QFileDialog, QMessageBox, QFormLayout, QCheckBox,
    QGroupBox, QProgressBar)
from .project import create_project, load_project, import_reference, save_project, verify_references
from .backend import blender_command
from .export import export_atlas
from .preview import GLBPreview


class Signals(QObject):
    done = Signal(object)
    fail = Signal(str)


class Task(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = Signals()

    @Slot()
    def run(self):
        try:
            self.signals.done.emit(self.operation())
        except Exception as exc:
            self.signals.fail.emit(f"{type(exc).__name__}: {exc}")


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GOSHMAN — Animatronic Character Studio [Alpha]")
        self.resize(1280, 850)
        self.folder: Path | None = None
        self.project = None
        self.blender = QProcess(self)
        self.blender.readyReadStandardOutput.connect(self.read_stdout)
        self.blender.readyReadStandardError.connect(self.read_stderr)
        self.blender.finished.connect(self.blender_finished)
        self.threads = QThreadPool.globalInstance()
        self._tasks = []
        self._ai_project_folder = None
        self.setup_ui()
        self.update_ui()

    def setup_ui(self):
        root = QWidget(); self.setCentralWidget(root)
        lay = QVBoxLayout(root)
        header = QHBoxLayout()
        title = QLabel("GOSHMAN  |  3D CHARACTER STUDIO")
        font = title.font(); font.setPointSize(18); font.setBold(True); title.setFont(font)
        header.addWidget(title); header.addStretch()
        for label, handler in (("Создать проект",self.new_project),("Открыть проект",self.open_project),
                               ("Добавить референсы",self.add_images)):
            b = QPushButton(label); b.clicked.connect(handler); header.addWidget(b)
        lay.addLayout(header)
        self.status = QLabel("Нет проекта"); lay.addWidget(self.status)
        main = QSplitter(Qt.Horizontal)
        lay.addWidget(main, 1)
        left = QWidget(); ll = QVBoxLayout(left)
        ll.addWidget(QLabel("Референсы персонажа"))
        self.images = QListWidget(); self.images.currentRowChanged.connect(self.show_image)
        ll.addWidget(self.images)
        self.preview = QLabel("Изображение будет показано здесь")
        self.preview.setMinimumSize(310,225); self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background: #232a31; color: #aaa; border-radius: 8px;")
        ll.addWidget(self.preview)
        prep=QPushButton("Подготовить 5 ракурсов")
        prep.clicked.connect(self.prepare_views)
        ll.addWidget(prep)
        main.addWidget(left)
        right = QTabWidget(); main.addWidget(right)
        tab_spec = QWidget(); form = QFormLayout(tab_spec)
        self.fields = {}
        for name, text, low, high, value in (("height","Высота (ед.)",.15,20,6.2),
            ("head_scale","Масштаб головы",.15,3,1),("snout_length","Длина морды",.15,3,1),
            ("tail_length","Длина хвоста",.15,10,2.4),("eye_scale","Масштаб глаз",.15,3,1)):
            from PySide6.QtWidgets import QDoubleSpinBox
            spin=QDoubleSpinBox();spin.setRange(low,high);spin.setDecimals(2);spin.setSingleStep(.05);spin.setValue(value)
            self.fields[name]=spin;form.addRow(text,spin)
        self.armor=QSpinBox(); self.armor.setRange(0,3); self.armor.setValue(2);form.addRow("Детализация брони",self.armor)
        btn=QPushButton("Сохранить параметры");btn.clicked.connect(self.save_spec);form.addWidget(btn)
        right.addTab(tab_spec,"Персонаж")
        tab_b=QWidget();v=QVBoxLayout(tab_b)
        self.blender_path=QLineEdit();self.blender_path.setPlaceholderText("C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe")
        choose=QPushButton("Найти blender.exe");choose.clicked.connect(self.pick_blender)
        v.addWidget(QLabel("Blender executable"));v.addWidget(self.blender_path);v.addWidget(choose)
        self.render_frames=QCheckBox("Рендерить PNG-анимации (медленно)");v.addWidget(self.render_frames)
        self.frame_size=QSpinBox();self.frame_size.setRange(128,2048);self.frame_size.setValue(512)
        v.addWidget(QLabel("Размер кадра, px"));v.addWidget(self.frame_size)
        self.pbr_resolution=QComboBox()
        for label,value in (("Выключено",0),("256 px — тест",256),
                            ("512 px",512),("1024 px",1024),("2048 px — высокое качество",2048)):
            self.pbr_resolution.addItem(label,value)
        self.pbr_resolution.setCurrentIndex(1)
        v.addWidget(QLabel("UV PBR-текстуры"));v.addWidget(self.pbr_resolution)
        generate=QPushButton("СОЗДАТЬ 3D-МОДЕЛЬ В BLENDER"); generate.clicked.connect(self.generate)
        v.addWidget(generate)
        self.abort_button=QPushButton("Прервать процесс");self.abort_button.clicked.connect(self.abort)
        v.addWidget(self.abort_button)
        atlas=QPushButton("Собрать доступные спрайт-листы"); atlas.clicked.connect(self.pack_existing)
        v.addWidget(atlas)
        open_output=QPushButton("Открыть папку экспорта");open_output.clicked.connect(self.open_output)
        v.addWidget(open_output)
        qa_button=QPushButton("Проверить экспорт (3D / PNG / анимации)")
        qa_button.clicked.connect(self.audit_output)
        v.addWidget(qa_button)
        v.addStretch()
        right.addTab(tab_b,"Генерация / Экспорт")
        ai=QWidget();av=QVBoxLayout(ai)
        av.addWidget(QLabel("GPT анализирует референсы, но не заменяет 3D-геометрию."))
        self.model_id=QLineEdit(os.getenv("GOSHMAN_OPENAI_MODEL","gpt-4.1"))
        av.addWidget(QLabel("ID модели, доступной через API"));av.addWidget(self.model_id)
        self.api_key_input=QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Ключ OpenAI API (сохраняется в защищённом хранилище ОС)")
        av.addWidget(self.api_key_input)
        key_button=QPushButton("Сохранить API-ключ")
        key_button.clicked.connect(self.save_ai_key)
        av.addWidget(key_button)
        self.consent=QCheckBox("Разрешаю передачу моих референсов в OpenAI для анализа")
        av.addWidget(self.consent)
        ai_btn=QPushButton("Проанализировать референсы");ai_btn.clicked.connect(self.analyze_ai)
        av.addWidget(ai_btn); av.addStretch()
        right.addTab(ai,"GPT")
        neural=QWidget();nv=QVBoxLayout(neural)
        nv.addWidget(QLabel("Multi-view AI → настоящий GLB (платный сервис, отдельное согласие)"))
        self.neural_provider=QComboBox()
        self.neural_provider.addItems(["meshy","tripo"])
        nv.addWidget(QLabel("AI-провайдер"));nv.addWidget(self.neural_provider)
        self.neural_api_key=QLineEdit()
        self.neural_api_key.setEchoMode(QLineEdit.Password)
        self.neural_api_key.setPlaceholderText("API-ключ провайдера (не сохраняется в проекте)")
        nv.addWidget(self.neural_api_key)
        self.allow_neural_upload=QCheckBox("Разрешаю передачу 4 приватных ракурсов выбранному провайдеру")
        self.allow_neural_cost=QCheckBox("Разрешаю платную генерацию в аккаунте провайдера")
        nv.addWidget(self.allow_neural_upload);nv.addWidget(self.allow_neural_cost)
        neural_btn=QPushButton("СОЗДАТЬ НАСТОЯЩУЮ 3D-МОДЕЛЬ ЧЕРЕЗ AI")
        neural_btn.clicked.connect(self.generate_neural)
        nv.addWidget(neural_btn)
        audit_btn=QPushButton("Проверить исходные 4 ракурса")
        audit_btn.clicked.connect(self.audit_ai_views)
        nv.addWidget(audit_btn)
        self.import_ai_btn=QPushButton("Импортировать AI GLB в редактируемый Blender-проект")
        self.import_ai_btn.clicked.connect(self.import_ai_glb)
        nv.addWidget(self.import_ai_btn)
        nv.addWidget(QLabel("После завершения GLB проверяется автоматически; точность по референсам и риг ещё требуют QA."))
        nv.addStretch()
        right.addTab(neural,"AI → 3D")
        preview_tab=QWidget();pv=QVBoxLayout(preview_tab)
        self.viewer=GLBPreview()
        pv.addWidget(self.viewer,1)
        refresh=QPushButton("Загрузить текущий GLB");refresh.clicked.connect(self.load_model_preview)
        pv.addWidget(refresh)
        right.addTab(preview_tab,"3D просмотр")
        main.addWidget(right);main.setSizes([460,760])
        lay.addWidget(QLabel("Журнал выполнения"))
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumBlockCount(5000)
        self.log.setMinimumHeight(140);lay.addWidget(self.log)
        self.progress=QProgressBar();self.progress.setRange(0,1);self.progress.setValue(0);lay.addWidget(self.progress)
        self.setStyleSheet("QMainWindow{background:#171b22;} QWidget{color:#eee;} QLineEdit,QListWidget,QPlainTextEdit,QSpinBox,QDoubleSpinBox{background:#252c35; color:#eee; padding:4px;} QPushButton{background:#354457; color:white; padding:8px; border-radius:5px;} QPushButton:hover{background:#476080;}")

    def note(self, message):
        self.log.appendPlainText(message.rstrip())

    def fail(self, message):
        self.note("ОШИБКА: " + message)
        QMessageBox.warning(self,"GOSHMAN",message)

    def update_ui(self):
        self.status.setText(str(self.folder) if self.folder else "Проект не открыт")
        self.images.clear()
        if self.project:
            for image in self.project.references:
                self.images.addItem(QListWidgetItem(image.role + " — " + Path(image.filename).name))
            for name, spin in self.fields.items():
                spin.setValue(getattr(self.project.spec,name))
            self.armor.setValue(self.project.spec.armor_detail)

    def new_project(self):
        path = QFileDialog.getExistingDirectory(self,"Выберите новую пустую папку проекта")
        if not path: return
        try:
            self.project=create_project(Path(path),"Animatronic Crocodile Cowboy")
            self.folder=Path(path);self.update_ui();self.note("Новый проект создан")
        except Exception as e: self.fail(str(e))

    def open_project(self):
        file,_=QFileDialog.getOpenFileName(self,"Открыть project.json",filter="project.json (project.json)")
        if not file: return
        try:
            self.folder=Path(file).parent;self.project=load_project(self.folder)
            self.update_ui();self.note("Проект открыт")
        except Exception as e:self.fail(str(e))

    def add_images(self):
        if not self.project: return self.fail("Сначала откройте проект")
        images,_=QFileDialog.getOpenFileNames(self,"Добавить референсы",filter="Images (*.png *.jpg *.jpeg *.webp)")
        try:
            for image in images:
                item=import_reference(self.folder,self.project,Path(image))
                self.note("Импорт: " + item.filename)
            self.update_ui()
        except Exception as e:self.fail(str(e))

    def show_image(self, index):
        if index < 0 or not self.project or index >= len(self.project.references):return
        path=self.folder/self.project.references[index].filename
        img=QPixmap(str(path))
        self.preview.setPixmap(img.scaled(self.preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))

    def prepare_views(self):
        if not self.folder:
            return self.fail("Проект не открыт")
        try:
            from .reference_views import prepare_turnaround
            manifest=prepare_turnaround(self.folder)
            self.note("Подготовлены ракурсы: "+", ".join(manifest["views"].keys()))
            self.note("Результат сохранён в derived/turnaround; это референсы, не готовая 3D-модель.")
        except Exception as exc:
            self.fail(str(exc))

    def save_spec(self):
        if not self.project:return self.fail("Проект не открыт")
        try:
            for key,w in self.fields.items(): setattr(self.project.spec,key,w.value())
            self.project.spec.armor_detail=self.armor.value()
            save_project(self.folder,self.project)
            self.note("Параметры сохранены")
        except Exception as e:self.fail(str(e))

    def pick_blender(self):
        file,_=QFileDialog.getOpenFileName(self,"blender.exe",filter="Programs (*.exe);;All Files (*)")
        if file:self.blender_path.setText(file)

    def generate(self):
        if not self.project:return self.fail("Проект не открыт")
        self.save_spec()
        if self.blender.state()!=QProcess.NotRunning:return self.fail("Blender уже работает")
        try:
            cmd=blender_command(self.folder,self.blender_path.text().strip() or None,
                                self.render_frames.isChecked(),True,self.frame_size.value(),
                                self.pbr_resolution.currentData())
            self._render_after=self.render_frames.isChecked()
            self.blender.start(cmd[0],cmd[1:])
            self.progress.setRange(0,0)
            self.note("Запуск Blender: "+cmd[0])
        except Exception as e:self.fail(str(e))

    def read_stdout(self):
        self.note(bytes(self.blender.readAllStandardOutput()).decode("utf-8",errors="replace"))

    def read_stderr(self):
        self.note(bytes(self.blender.readAllStandardError()).decode("utf-8",errors="replace"))

    def load_model_preview(self):
        if not self.folder:
            return self.fail("Проект не открыт")
        model = self.folder/"output"/"crocodile_cowboy.glb"
        try:
            info=self.viewer.load_glb(model)
            self.note(f"3D preview: {info['mesh_nodes']} узлов, {info['preview_faces']} треугольников")
        except Exception as e:
            self.fail(str(e))

    def blender_finished(self,code,status):
        self.progress.setRange(0,1);self.progress.setValue(1 if code==0 else 0)
        self.note("Blender завершился с кодом "+str(code))
        if code==0:
            self.load_model_preview()
            if self._render_after:self.pack_existing()

    def abort(self):
        if self.blender.state()!=QProcess.NotRunning:
            self.blender.terminate()
            self.note("Запрошено завершение Blender")

    def pack_existing(self):
        if not self.folder:return self.fail("Проект не открыт")
        out=self.folder/"output"/"sprites"
        if not out.exists():return self.fail("Нет PNG-анимаций")
        try:
            for directory in sorted(p for p in out.iterdir() if p.is_dir()):
                if list(directory.glob("*.png")):
                    result=export_atlas(directory,out/(directory.name+"_sheet.png"),directory.name,24,6)
                    self.note(f"Атлас: {directory.name}: {result['frames']} кадров")
        except Exception as e:self.fail(str(e))

    def open_output(self):
        if not self.folder:return self.fail("Проект не открыт")
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        out=self.folder/"output"
        out.mkdir(exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(out)))

    def audit_output(self):
        if not self.folder:
            return self.fail("Проект не открыт")
        try:
            from .quality import audit_project
            report = audit_project(self.folder)
            self.note("Проверка экспорта: " + report["status"])
            self.note("GLB: " + json.dumps(report["glb"], ensure_ascii=False))
            for warning in report["warnings"]:
                self.note("ПРЕДУПРЕЖДЕНИЕ: " + warning)
            for error in report["errors"]:
                self.note("ОШИБКА: " + error)
            if report["errors"]:
                QMessageBox.warning(self, "Проверка GOSHMAN", "Найдены ошибки: " + str(len(report["errors"])))
            else:
                QMessageBox.information(self, "Проверка GOSHMAN", "Технические проверки пройдены. Визуальное сходство с референсами не подтверждено.")
        except Exception as exc:
            self.fail(str(exc))

    def audit_ai_views(self):
        if not self.folder:
            return self.fail("Проект не открыт")
        try:
            from .reference_preflight import audit_multiview_inputs
            report=audit_multiview_inputs(self.folder)
            self.note(f"Четыре исходных AI-ракурса: {report['status']}")
            for warning in report["warnings"]:
                self.note("ПРЕДУПРЕЖДЕНИЕ: "+warning)
            for error in report["errors"]:
                self.note("ОШИБКА: "+error)
        except Exception as exc:
            self.fail(str(exc))

    def import_ai_glb(self):
        if not self.folder or not self.project:
            return self.fail("Проект не открыт")
        # Allows an already downloaded mesh, even when a provider API is unavailable.
        start=str(self.folder/"output"/"reconstruction")
        asset,_=QFileDialog.getOpenFileName(self,"Выберите реальный GLB-меш",start,
                                            "glTF Binary (*.glb)")
        if not asset:
            return
        try:
            from .quality import inspect_glb
            from .backend import find_blender, import_external_glb
            source=Path(asset).resolve(strict=True)
            result=inspect_glb(source)
            if result["meshes"]<1:
                raise ValueError("В GLB не обнаружено геометрии")
            # Filenames derived from hash avoid overwriting other imported versions.
            from .project import sha256_file
            digest=sha256_file(source)[:16]
            destination=self.folder/"output"/"reconstruction"/"imports"/(digest+".blend")
            if destination.exists():
                self.note("BLEND уже подготовлен: "+str(destination))
                return
            blender_path=str(find_blender(self.blender_path.text().strip() or None))
            project_folder=self.folder
            requested_height=float(self.fields["height"].value())
            def convert():
                operation=import_external_glb(source,destination,
                            blender_path=blender_path,height=requested_height)
                return {"returncode":operation.returncode,"stdout":operation.stdout,
                        "stderr":operation.stderr,"destination":str(destination),
                        "project":str(project_folder)}
            task=Task(convert)
            task.signals.done.connect(self.import_ai_finished)
            task.signals.fail.connect(self.fail)
            self._tasks.append(task);self.threads.start(task)
            self.note("Импорт AI GLB в Blender запущен без изменения исходного файла")
        except Exception as exc:
            self.fail(str(exc))

    def import_ai_finished(self,result):
        if result["returncode"] != 0:
            self.fail("Blender не смог импортировать GLB. "+
                      str(result.get("stderr",""))[-1200:])
            return
        file=Path(result["destination"])
        if not file.is_file():
            return self.fail("Blender завершился, но файл .blend отсутствует")
        self.note("Редактируемый Blender-проект создан: "+str(file))
        if self.folder is not None and str(self.folder)==result["project"]:
            self.note("Исходный GLB сохранён без изменений; сходство с референсами ещё не подтверждено.")

    def generate_neural(self):
        if not self.folder or not self.project:
            return self.fail("Сначала откройте проект")
        if not self.allow_neural_upload.isChecked() or not self.allow_neural_cost.isChecked():
            return self.fail("Требуются отдельные разрешения на передачу референсов и платный AI-запрос")
        provider=self.neural_provider.currentText()
        key=self.neural_api_key.text().strip() or None
        decision=QMessageBox.question(self,"Подтверждение платного AI-задания",
            "Передать четыре вида крокодила сервису "+provider+
            " и запустить платное создание 3D-модели? Расходы определяются тарифом провайдера.",
            QMessageBox.Yes | QMessageBox.No,QMessageBox.No)
        if decision != QMessageBox.Yes:
            return
        from .reconstruction import run_multiview_job
        root=self.folder
        self.neural_api_key.clear()
        task=Task(lambda: run_multiview_job(root,provider,
            approve_upload=True,approve_billing=True,api_key=key))
        task.signals.done.connect(lambda report:self.neural_done(root,provider,report))
        task.signals.fail.connect(self.fail)
        self._tasks.append(task)
        self.threads.start(task)
        self.note("AI-генерация запущена. Результат будет проверен как реальный GLB.")

    def neural_done(self,root,provider,report):
        self.note("AI "+provider+": "+report.get("status","UNKNOWN"))
        if report.get("reason"):
            self.note(report["reason"])
        if report.get("status") != "PASS_TECHNICAL":
            return
        if self.folder != root:
            self.note("Новый проект открыт; результат сохранён только в исходном проекте.")
            return
        job=report.get("input_sha256","")[:16]
        path=root/"output"/"reconstruction"/provider/job/"model.glb"
        try:
            result=self.viewer.load_glb(path)
            self.note("Настоящий GLB загружен: "+str(result.get("mesh_nodes",0))+" меш-узлов.")
        except Exception as exc:
            self.fail("Проверенный AI GLB есть на диске, но GUI просмотр не удался: "+str(exc))

    def save_ai_key(self):
        key=self.api_key_input.text().strip()
        if not key:
            return self.fail("Введите API-ключ")
        try:
            from .ai import save_api_key
            save_api_key(key)
            self.api_key_input.clear()
            self.note("API-ключ сохранён в системном хранилище. В project.json ключ не записывается.")
        except Exception as exc:
            self.fail(f"Не удалось сохранить API-ключ: {exc}")

    def analyze_ai(self):
        if not self.project:return self.fail("Проект не открыт")
        if not self.consent.isChecked():return self.fail("Подтвердите отправку референсов в OpenAI")
        from .ai import analyze_references
        paths=[self.folder/r.filename for r in self.project.references]
        if not paths:return self.fail("Нет референсов")
        roles=[record.role for record in self.project.references]
        self._ai_project_folder=self.folder
        task=Task(lambda: analyze_references(paths,self.model_id.text().strip(),consent=True,roles=roles))
        task.signals.done.connect(self.ai_done);task.signals.fail.connect(self.fail)
        self._tasks.append(task);self.threads.start(task)
        self.note("AI-анализ запущен, ждём проверяемую структуру ответа")

    def ai_done(self,result):
        if self.folder != self._ai_project_folder or not self.project:
            self.note("GPT результат получен для другого проекта и не применён.")
            return
        proposed=result["spec"]
        old=self.project.spec
        changes=[]
        for field in ("height","head_scale","snout_length","tail_length","eye_scale","armor_detail"):
            current=getattr(old,field)
            suggested=getattr(proposed,field)
            if current != suggested:
                changes.append(f"{field}: {current} → {suggested}")
        uncertainties=result.get("uncertainties",[])
        explanation="\n".join(changes) if changes else "Измеримые параметры не изменятся."
        if uncertainties:
            explanation += "\n\nНеопределённости:\n" + "\n".join("• " + str(x) for x in uncertainties)
        answer=QMessageBox.question(self,"Подтвердить параметры GPT",
            "Применить предложенные изменения к проекту?\n\n"+explanation,
            QMessageBox.Yes | QMessageBox.No,QMessageBox.No)
        if answer != QMessageBox.Yes:
            self.note("Предложения GPT отклонены, существующие параметры сохранены.")
            return
        self.project.spec=proposed
        save_project(self.folder,self.project)
        self.update_ui()
        self.note("GPT параметры применены после подтверждения.")


def main():
    app=QApplication(sys.argv)
    window=Window();window.show()
    return app.exec()

if __name__=="__main__":
    sys.exit(main())
