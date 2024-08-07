from maya import cmds
import maya.api.OpenMaya as om
from logic.archive import Archive


class MainUi:

    def __init__(self) -> None:
        self.create_ui()

    def create_ui(self):
        if cmds.window("customUI", exists=True):
            cmds.deleteUI("customUI", window=True)

        window = cmds.window("customUI", title="Archive", widthHeight=(400, 200))
        form = cmds.formLayout()

        # Radio buttons in a row layout
        radio_row = cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 200))
        self.radio_col = cmds.radioCollection()
        cmds.radioButton('folder', label='FOLDER', select=True)
        cmds.radioButton('file', label='FILE')
        cmds.setParent('..')

        # First row of UI elements
        row1 = cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)
        cmds.button(label='Clear', command=lambda x: self.clear_text_field('source_path_field'))
        self.source_path_field = cmds.textFieldGrp('source_path_field', label='Get Source Path', text='')
        cmds.button(label='Browse', command=lambda x: self.browse_source('source_path_field'))
        cmds.setParent('..')

        # Second row of UI elements
        row2 = cmds.rowLayout(numberOfColumns=3, adjustableColumn=2)
        cmds.button(label='Clear', command=lambda x: self.clear_text_field('archiving_path_field'))
        self.archiving_path_field = cmds.textFieldGrp('archiving_path_field', label='Set Archiving Path', text='')
        cmds.button(label='Browse', command=lambda x: self.browse_archive('archiving_path_field'))
        cmds.setParent('..')

        # Apply button
        self.apply_button = cmds.button(label='START ARCHIVING', height=30, command=self.start_archive)

        # Arrange elements in the form layout
        cmds.formLayout(form, edit=True,
                        attachForm=[
                            (radio_row, 'top', 10), (radio_row, 'left', 10), (radio_row, 'right', 10),
                            (row1, 'left', 10), (row1, 'right', 10),
                            (row2, 'left', 10), (row2, 'right', 10),
                            (self.apply_button, 'left', 10), (self.apply_button, 'right', 10), (self.apply_button, 'bottom', 10)
                        ],
                        attachControl=[
                            (row1, 'top', 10, radio_row),
                            (row2, 'top', 10, row1),
                            (self.apply_button, 'top', 10, row2)
                        ])

        cmds.showWindow(window)

    def clear_text_field(self, text_field):
        cmds.textFieldGrp(text_field, edit=True, text='')

    def browse_source(self, text_field):

        mode = cmds.radioCollection(self.radio_col, query = True, select = True)

        if mode == 'folder':
            source_path = cmds.fileDialog2(fileMode=2, caption="Select Folder", startingDirectory=r'\\GANDALF\3d4_23_24\COUPDESOLEIL\09_publish')
            if source_path:
                cmds.textFieldGrp(text_field, edit=True, text=source_path[0])
            return

        else: # 'file'
            source_path = cmds.fileDialog2(fileMode=4, caption="Select File", fileFilter='*.ma;*.mb', startingDirectory=r'\\GANDALF\3d4_23_24\COUPDESOLEIL\09_publish')
            if source_path:
                cmds.textFieldGrp(text_field, edit=True, text=source_path[0])
            return


    def browse_archive(self, text_field):
        archive_path = cmds.fileDialog2(fileMode=2, caption="Select Folder", startingDirectory=r'\\GANDALF\3d4_23_24\ARCHIVAGE\COUP-DE-SOLEIL')
        if archive_path:
            cmds.textFieldGrp(text_field, edit=True, text=archive_path[0])


    def start_archive(self, button: str):

        source_path: str = cmds.textFieldGrp(self.source_path_field, query=True, text=True)
        archive_path: str = cmds.textFieldGrp(self.archiving_path_field, query=True, text=True)

        if '3d4_23_24/COUPDESOLEIL' in archive_path:
            cmds.confirmDialog(message='You must not archive in CDS directory.', icon='critical', button='OK')
            return

        om.MGlobal.displayInfo(f'Source Path: {source_path}')
        om.MGlobal.displayInfo(f'Archive Path: {archive_path}')

        if cmds.radioCollection(self.radio_col, query = True, select = True) == 'folder':
            archive_tool: Archive = Archive(source_path=source_path, archive_path=archive_path)
            om.MGlobal.displayInfo(f'archive_tool.archive_files()')
            archive_tool.archive_files()

        else: # 'file'
            archive_tool: Archive = Archive(source_path=source_path, archive_path=archive_path)
            om.MGlobal.displayInfo(f'archive_tool.archive_file()')
            archive_tool.archive_file(source_path, archive_path)
            cmds.file(new=True, force=True)
