import logging
import os
import shutil
from maya import cmds, mel
from .logger import Logger


class Archive:


    def __init__(self, source_path: str = '', archive_path: str = ''):

        self.SOURCE_PATH: str = source_path.replace('/', '\\')
        self.ARCHIVE_PATH: str = archive_path.replace('/', '\\')
        self.Z_STRING: str = 'Z:'
        self.CDS_STRING: str = r'\\GANDALF\3d4_23_24\COUPDESOLEIL'
        self.CDS_STRING_SHORT: str = r'3d4_23_24\COUPDESOLEIL'
        self.TEXTURE_ROOT_DIRPATH: str = r'\\GANDALF\3d4_23_24\COUPDESOLEIL\10_texture'
        self.TEXTURE_ROOT_DIRNAME: str = '10_texture'
        self.CDS_NAME: str = 'COUPDESOLEIL'
        self.UDIM_TOKEN: str = '<udim>'
        self.UV_TOKEN: str = 'u<u>_v<v>'
        self.WORKSPACE_TOKEN: str = '<ws>'
        self.RIB_STRING: str = 'rib'
        self.MAYA_PROJECT_DIRPATH: str = r'\\GANDALF\3d4_23_24\COUPDESOLEIL\02_ressource\@DAVID\ARCHIVAGE\ArchivingTools\project_files\maya'

        self.logger: Logger = Logger()
        self.LOG_PATH: str = os.path.join(self.ARCHIVE_PATH, 'archive.log')
        if not os.path.exists(self.LOG_PATH):
            self.logger.write_to_file(path = self.LOG_PATH, level=logging.INFO)

        self.CACHE_DICT: dict = {
            'AlembicNode': 'abc_File',
            'file': 'fileTextureName',
            'gpuCache': 'cacheFileName',
            'xgmSplineCache': 'fileName'
        }


    def load_plugins(self) -> None:

        plugin_name: str = 'RenderMan_for_Maya'
        if not cmds.pluginInfo(plugin_name, query=True, loaded=True):
            cmds.loadPlugin(plugin_name)


    def set_project(self) -> str:
        
        scene_path = cmds.file(query = True, sceneName = True)
        if scene_path == '':
            cmds.error('No project found.')
            return
        maya_path = scene_path.split('scenes')[0][:-1]
        mel.eval(f'setProject "{maya_path}";')
        self.logger.info(f'Set project : {maya_path}')
        return maya_path


    def list_renderman_nodes(self) -> list:

        nodes_to_return: list = []

        pxr_texture_nodes = cmds.ls(type = 'PxrTexture') # filename
        pxr_ptexture_nodes = cmds.ls(type = 'PxrPtexture') # filename
        pxr_normalmap_nodes = cmds.ls(type = 'PxrNormalMap') # filename

        nodes_to_return = pxr_texture_nodes + pxr_ptexture_nodes + pxr_normalmap_nodes

        return nodes_to_return


    def list_rib_nodes(self):
        return cmds.ls(type = 'RenderManArchive') # filename


    def list_gpu_cache_nodes(self) -> list:
        return cmds.ls(type = 'gpuCache') # cacheGeomPath


    def list_file_nodes(self) -> list:
        return cmds.ls(type = 'file') # fileTextureName


    def list_alembic_nodes(self) -> list:
        return cmds.ls(type='AlembicNode') # abc_File


    def list_xgen_cache(self) -> list:
        return cmds.ls(type='xgmSplineCache') # fileName


    def list_files(self, dirpath: str) -> list:

        files = []
        for filename in os.listdir(dirpath):
            filepath = os.path.join(dirpath, filename)
            if not os.path.isfile(filepath):
                continue
            files.append(filepath)
        return files


    def get_relative_path_until(self, filepath: str, stop_dir: str) -> str:

        parts = filepath.replace('/', '\\').split(os.sep)
        try:
            stop_index = parts.index(stop_dir)
        except ValueError:
            raise ValueError(f"'{stop_dir}' not found in the filepath")
        
        relative_parts = parts[stop_index + 2:-1]
        relative_path = os.path.join(*relative_parts).replace('/', '\\')
        return relative_path


    def find_files_witch_match(self, parent_dirpath: str, match_string: str) -> list:

        files = []
        for file in os.listdir(parent_dirpath):
            if match_string in file:
                files.append(os.path.join(parent_dirpath, file))
        return files


    def archive_texture(self, texture_node: str, sourceimages_dirpath: str, current_project: str) -> None:

        texture_filepath_attribute: str = cmds.getAttr(f'{texture_node}.filename').replace('/', '\\') # example : \\GANDALF\3d4_23_24\COUPDESOLEIL\10_texture\04_enviro\bat02\map\CDS_glycinePlante_DiffuseColor_ACES - ACEScg.1001.png
        if not texture_filepath_attribute or texture_filepath_attribute == '':
            self.logger.error(f'{texture_node}.filename attribute is empty.')
            return
        if self.TEXTURE_ROOT_DIRNAME not in texture_filepath_attribute:
            self.logger.warning(f'Texture file {texture_filepath_attribute} not in texture folder.')
        if self.Z_STRING in texture_filepath_attribute:
            texture_filepath_attribute = texture_filepath_attribute.replace(self.Z_STRING, self.CDS_STRING)
            self.logger.warning(f'Texture file {texture_filepath_attribute} is set on Z: network drive.')
        texture_filename_attribute: str = os.path.basename(texture_filepath_attribute) # example : CDS_glycinePlante_DiffuseColor_ACES - ACEScg.1001.png
        texture_parent_directory: str = os.path.dirname(texture_filepath_attribute) # example : \\GANDALF\3d4_23_24\COUPDESOLEIL\10_texture\04_enviro\bat02\map
        self.logger.info(f'Texture filepath attribute: {texture_filepath_attribute}')

        texture_filepath: str = texture_filepath_attribute # example : //gandalf/3d4_23_24/COUPDESOLEIL/10_texture/04_enviro/bat01/maps/CDS_bat01_A_gouttiere_Height_Utility - Raw.png
        texture_filename: str = os.path.basename(texture_filepath) # example : CDS_bat01_A_gouttiere_Height_Utility - Raw.png
        self.logger.info(f'Texture Filepath: {texture_filepath}')
        self.logger.info(f'Texture Filename: {texture_filename}')

        # recreate the texture tree in the archive maya project
        intermediate_dirs = self.get_relative_path_until(filepath=texture_filepath, stop_dir=self.CDS_NAME)
        self.logger.info(f'Intermediate Dirs: {intermediate_dirs}')
        texture_archive_parent_dirpath: str = os.path.join(sourceimages_dirpath, *intermediate_dirs.split('\\'))
        if not os.path.exists(texture_archive_parent_dirpath):
            os.makedirs(texture_archive_parent_dirpath)
        self.logger.info(f'Texture Archive Parent Dirpath: {texture_archive_parent_dirpath}')

        # set texture in filename attribute
        texture_filepath_attribute_archive: str = os.path.join(texture_archive_parent_dirpath, texture_filename_attribute).replace(current_project, self.WORKSPACE_TOKEN).replace('\\', '/')
        cmds.setAttr(f'{texture_node}.filename', texture_filepath_attribute_archive, type='string')
        self.logger.info(f'setAttr {texture_node}.filename {texture_filepath_attribute_archive}')

        if not self.UDIM_TOKEN in texture_filepath_attribute and not self.UV_TOKEN in texture_filepath_attribute:
            if not os.path.exists(texture_filepath):
                self.logger.error(f'{texture_filepath} texture file does not exists.')
                return
            # copy texture file
            texture_filepath_archive: str = os.path.join(texture_archive_parent_dirpath, texture_filename)
            if not os.path.exists(texture_filepath_archive):
                shutil.copy(texture_filepath, texture_archive_parent_dirpath)
                self.logger.info(f'Copy : {texture_filepath} -> {texture_archive_parent_dirpath}')
            self.logger.info(f'Texture Filepath Archive: {texture_filepath_archive}')

            # copy .tex file
            tex_file: str = f'{texture_filepath}.tex'
            if os.path.exists(tex_file):
                if not os.path.exists(os.path.join(texture_archive_parent_dirpath, tex_file)):
                    shutil.copy(tex_file, texture_archive_parent_dirpath)
                    self.logger.info(f'Copy: {tex_file} -> {texture_archive_parent_dirpath}')
            return
        
        if self.UDIM_TOKEN in texture_filepath_attribute:
            match_string = texture_filename_attribute.split(self.UDIM_TOKEN)[0]
            for texture_filepath_udim in self.find_files_witch_match(parent_dirpath=texture_parent_directory, match_string=match_string):
                if not os.path.exists(texture_filepath_udim):
                    self.logger.error(f'{texture_filepath_udim} texture file does not exists.')
                    continue
                texture_filename_udim: str = os.path.basename(texture_filepath_udim)
                if not os.path.exists(os.path.join(texture_archive_parent_dirpath, texture_filename_udim)):
                    shutil.copy(texture_filepath_udim, texture_archive_parent_dirpath)
                    self.logger.info(f'Copy: {texture_filepath_udim} -> {texture_archive_parent_dirpath}')
            return

        if self.UV_TOKEN in texture_filepath_attribute:
            match_string = texture_filename_attribute.split(self.UV_TOKEN)[0]
            for texture_filepath_udim in self.find_files_witch_match(parent_dirpath=texture_parent_directory, match_string=match_string):
                if not os.path.exists(texture_filepath_udim):
                    self.logger.error(f'{texture_filepath_udim} texture file does not exists.')
                    continue
                texture_filename_udim: str = os.path.basename(texture_filepath_udim)
                if not os.path.exists(os.path.join(texture_archive_parent_dirpath, texture_filename_udim)):
                    shutil.copy(texture_filepath_udim, texture_archive_parent_dirpath)
                    self.logger.info(f'Copy: {texture_filepath_udim} -> {texture_archive_parent_dirpath}')
            return


    def archive_cache(self, cache_node: str, cache_dirpath: str) -> None:

        cache_attribute: str = self.CACHE_DICT.get(cmds.nodeType(cache_node))

        cache_filepath_attribute: str = cmds.getAttr(f'{cache_node}.{cache_attribute}')
        if not os.path.exists(cache_filepath_attribute):
            self.logger.error(f'{cache_filepath_attribute} cache file does not exists.')
            return
        
        if self.Z_STRING in cache_filepath_attribute:
            self.logger.warning(f'{cache_filepath_attribute} is set on Z: network drive.')
            cache_filepath_attribute = cache_filepath_attribute.replace(self.Z_STRING, self.CDS_STRING)

        cache_filename: str = os.path.basename(cache_filepath_attribute)
        cache_filepath_archive: str = os.path.join(cache_dirpath, cache_filename)
        if not os.path.exists(cache_filepath_archive):
            shutil.copy(cache_filepath_attribute, cache_dirpath)
            self.logger.info(f'Copy: {cache_filepath_attribute} -> {cache_dirpath}')
        
        cmds.setAttr(f'{cache_node}.{cache_attribute}', cache_filepath_archive, type='string')
        self.logger.info(f'setAttr {cache_node}.{cache_attribute} {cache_filepath_archive}')


    def archive_rib(self, rib_node: str, cache_dirpath: str, current_project: str):

        rib_filepath_attribute: str = cmds.getAttr(f'{rib_node}.filename')
        if self.Z_STRING in rib_filepath_attribute:
            self.logger.warning(f'{rib_filepath_attribute} is set on Z: network drive.')
            rib_filepath_attribute = rib_filepath_attribute.replace(self.Z_STRING, self.CDS_STRING)

        rib_files_parent_dirpath: str = os.path.dirname(rib_filepath_attribute)
        rib_filename_attribute: str = os.path.basename(rib_filepath_attribute) # example: CDS_buissonLavandeA.<f>.rib
        rib_name: str = rib_filename_attribute.split('.')[0] # example: CDS_buissonLavandeA

        rib_archive_dirpath: str = os.path.join(cache_dirpath, self.RIB_STRING, rib_name)
        if not os.path.exists(rib_archive_dirpath):
            os.makedirs(rib_archive_dirpath)
            self.logger.info(f'Create rib directory: {rib_archive_dirpath}')
        
        for rib_filename in os.listdir(rib_files_parent_dirpath):
            if not rib_filename.endswith('.rib'):
                continue
            if not rib_filename.startswith(rib_name):
                continue
            rib_filepath: str = os.path.join(rib_files_parent_dirpath, rib_filename)
            rib_file_path_archive: str = os.path.join(rib_archive_dirpath, rib_filename)
            if not os.path.exists(rib_file_path_archive):
                shutil.copy(rib_filepath, rib_archive_dirpath)
                self.logger.info(f'Copy: {rib_filepath} -> {rib_archive_dirpath}')

        rib_filepath_attribute_archive: str = os.path.join(rib_archive_dirpath, rib_filename_attribute).replace(current_project, self.WORKSPACE_TOKEN)
        cmds.setAttr(f'{rib_node}.filename', rib_filepath_attribute_archive, type='string')
        self.logger.info(f'setAttr {rib_node}.filename {rib_filepath_attribute_archive}')
        

    def import_all_references(self):
        references = cmds.file(query=True, reference=True)
        
        if not references:
            return
        for ref in references:
            try:
                cmds.file(ref, importReference=True)
                self.logger.info(f'{ref} Reference Imported.')
            except:
                self.logger.error(f'Fail Import: {ref}')

            cmds.file(rename=cmds.file(query=True, sceneName=True))
            cmds.file(save=True, force=True)


    def archive_file(self, source_path: str, archiving_dirpath: str) -> None:

        self.load_plugins()

        self.logger.info(f'START ARCHIVING FILE: {source_path} ----------------------------------------------')
        self.logger.info(f'Publish Filepath: {source_path}')

        publish_filename: str = os.path.basename(source_path) # example: CDS_env_eglise_ldv_P.ma
        if 'seq' in publish_filename:
            asset_name: str = publish_filename.split('.')[0] # example: CDS_seq030_sh080_render_P
        else:
            asset_name: str = publish_filename.split('_')[2] # example: eglise
        self.logger.info(f'Asset Name: {asset_name}')

        archived_asset_dirpath: str = os.path.join(archiving_dirpath, asset_name)
        if not os.path.exists(archived_asset_dirpath):
            os.mkdir(archived_asset_dirpath)
        self.logger.info(f'Archived Asset Dirpath: {archived_asset_dirpath}')

        archived_asset_maya_dirpath: str = os.path.join(archived_asset_dirpath, 'maya')
        if not os.path.exists(archived_asset_maya_dirpath):
            shutil.copytree(self.MAYA_PROJECT_DIRPATH, archived_asset_maya_dirpath)
        self.logger.info(f'Archived Asset Maya Dirpath: {archived_asset_maya_dirpath}')
        archived_asset_sourceimages_dirpath: str = os.path.join(archived_asset_maya_dirpath, 'sourceimages')
        archived_asset_cache_dirpath: str = os.path.join(archived_asset_maya_dirpath, 'cache')
        self.logger.info(f'Archived Asset Sourceimages Dirpath: {archived_asset_sourceimages_dirpath}')

        archived_asset_filepath: str = os.path.join(archived_asset_maya_dirpath, 'scenes', publish_filename)
        if not os.path.exists(archived_asset_filepath):
            shutil.copy(source_path, archived_asset_filepath)
        self.logger.info(f'Archived Asset Filepath: {archived_asset_filepath}')

        cmds.file(archived_asset_filepath, open=True, force=True)
        current_project = self.set_project().replace('/', '\\')

        for texture_node in self.list_renderman_nodes():
            self.logger.info(f'Texture Node: {texture_node} ------------------------------------------------------')
            self.archive_texture(texture_node=texture_node, sourceimages_dirpath=archived_asset_sourceimages_dirpath, current_project=current_project)

        for rib_node in self.list_rib_nodes():
            self.logger.info(f'Rib Node: {rib_node} ------------------------------------------------------')
            self.archive_rib(rib_node=rib_node, cache_dirpath=archived_asset_cache_dirpath, current_project=current_project)

        for cache_node in self.list_alembic_nodes() + self.list_gpu_cache_nodes() + self.list_xgen_cache():
            self.logger.info(f'Cache Node: {cache_node} ------------------------------------------------------')
            self.archive_cache(cache_node=cache_node, cache_dirpath=archived_asset_cache_dirpath)

        for file_node in self.list_file_nodes():
            self.logger.info(f'File Node: {file_node} ------------------------------------------------------')
            self.archive_cache(cache_node=file_node, cache_dirpath=archived_asset_sourceimages_dirpath)

        self.import_all_references()

        cmds.file(save=True, force=True)


    def archive_files(self, iteration = None, start = None) -> None:

        self.load_plugins()

        publish_files: list = self.list_files(dirpath=self.SOURCE_PATH)

        if iteration:
            publish_files = publish_files[start:iteration]

        for publish_file in publish_files:
            self.archive_file(source_path=publish_file, archiving_dirpath=self.ARCHIVE_PATH)

        cmds.file(new=True, force=True)
        self.logger.info('End Archiving Files. -----------------------------------------------------------------------')
        cmds.confirmDialog(message='Archiving done.', messageAlign='left', icon='information', button='OK')


if __name__ == '__main__':

    PUBLISH_DIRPATH: str = r'\\GANDALF\3d4_23_24\COUPDESOLEIL\09_publish\asset\01_character\ldv'
    ARCHIVING_DIRPATH: str = r'\\GANDALF\3d4_23_24\ARCHIVAGE\COUP-DE-SOLEIL\2_ASSETS\A_CHARAS'

    archive_tool: Archive = Archive(source_path=PUBLISH_DIRPATH, archive_path=ARCHIVING_DIRPATH)
