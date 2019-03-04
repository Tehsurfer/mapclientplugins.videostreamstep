
"""
MAP Client Plugin Step
"""
import json

import cv2

from PySide import QtGui, QtCore

from mapclient.mountpoints.workflowstep import WorkflowStepMountPoint
from mapclientplugins.videostreamstep.configuredialog import ConfigureDialog

from opencmiss.zincwidgets.basesceneviewerwidget import BaseSceneviewerWidget


class readVideo(object):

    def __init__(self, filename, context):
        self._filename = filename
        self._context = context
        self._image_field = None
        self._fps = 0
        self._total_frame = 0
        self._image_dimension = None
        self._current_frame = 0
        self.cap = None
        self._material = None
        self.captureVideo()

    def play(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self._playVideoFrame)
        timer.start(1000 / self._fps)

    def _playVideoFrame(self):
        if self.cap.isOpened():
            flag, capture = self.cap.read()
            if flag is False:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                flag, capture = self.cap.read()
            self._image_field.setBuffer(capture.tobytes())
            self._current_frame = self._current_frame + 1

    def captureVideo(self):
        if not self.cap:
            self.cap = cv2.VideoCapture(self._filename)
        self._fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self._total_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if self.cap.isOpened():
            flag, capture = self.cap.read()
            self._image_dimension = self._loadFrames(capture)

    def _loadFrames(self, capture2):
        width = capture2.shape[1]
        height = capture2.shape[0]
        size = capture2.size
        itemsize = capture2.itemsize
        if not self._image_field:
            region = self._context.getDefaultRegion()
            field_module = region.getFieldmodule()
            self._image_field = field_module.createFieldImage()
            self._image_field.setSizeInPixels([width, height, 1])
            self._image_field.setPixelFormat(self._image_field.PIXEL_FORMAT_BGR)
            self._image_field.setBuffer(capture2.tobytes())
            material_module = self._context.getMaterialmodule()
            self._material = material_module.createMaterial()
            self._material.setTextureField(1, self._image_field)
        return [width, height]


class FrameContextData(object):

    def __init__(self, context, video_file_name, frames_per_second, framecount, image_dimensions):
        self._context = context
        self._shareable_widget = BaseSceneviewerWidget()
        self._shareable_widget.set_context(context)
        self._frames_per_second = frames_per_second
        self._video_file_name = video_file_name
        self._image_dimensions = image_dimensions
        self._framecount = framecount

    def get_context(self):
        return self._context

    def get_shareable_open_gl_widget(self):
        return self._shareable_widget

    def get_frames_per_second(self):
        return self._frames_per_second

    def get_frame_count(self):
        return self._framecount

    def get_video_file_name(self):
        return self._video_file_name

    def get_image_dimensions(self):
        return self._image_dimensions


class videostreamStep(WorkflowStepMountPoint):
    """
    Skeleton step which is intended to be a helpful starting point
    for new steps.
    """

    def __init__(self, location):
        super(videostreamStep, self).__init__('videostream', location)
        self._configured = False # A step cannot be executed until it has been configured.
        self._category = 'Utility'
        # Add any other initialisation code here:
        self._icon =  QtGui.QImage(':/videostreamstep/images/utility.png')
        # Ports:
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#image_context_data'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#uses',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#file_location'))

        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#provides',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#video_object'))
        self.addPort(('http://physiomeproject.org/workflow/1.0/rdf-schema#port',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#provides',
                      'http://physiomeproject.org/workflow/1.0/rdf-schema#image_context_data'))
        # Port data:
        self._image_context_data_input = None
        self._file_location = None # file_location

        self._video_object = None # <not-set>
        self._image_context_data_output = None # image_context_data

        # Config:
        self._config = {}
        self._config['identifier'] = ''

    def execute(self):
        """
        Add your code here that will kick off the execution of the step.
        Make sure you call the _doneExecution() method when finished.  This method
        may be connected up to a button in a widget for example.
        """
        # Put your execute step code here before calling the '_doneExecution' method.
        context = self._image_context_data_input
        filename = self._file_location
        video_object = readVideo(filename, context)
        fps, framecount, imagedimension = video_object._fps, video_object._total_frame, video_object._image_dimension
        framecontextdata = FrameContextData(context, filename, fps, framecount, imagedimension)

        self._image_context_data_output = framecontextdata
        self._video_object = video_object

        self._doneExecution()

    def setPortData(self, index, dataIn):
        """
        Add your code here that will set the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        uses port for this step then the index can be ignored.

        :param index: Index of the port to return.
        :param dataIn: The data to set for the port at the given index.
        """
        if index == 0:
            self._image_context_data_input = dataIn  # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location
        elif index == 1:
            self._file_location = dataIn  # http://physiomeproject.org/workflow/1.0/rdf-schema#context

    def getPortData(self, index):
        """
        Add your code here that will return the appropriate objects for this step.
        The index is the index of the port in the port list.  If there is only one
        provides port for this step then the index can be ignored.

        :param index: Index of the port to return.
        """
        if index == 2:
            return self._video_object  # http://physiomeproject.org/workflow/1.0/rdf-schema#file_location
        elif index == 3:
            return self._image_context_data_output  # http://physiomeproject.org/workflow/1.0/rdf-schema#context

    def configure(self):
        """
        This function will be called when the configure icon on the step is
        clicked.  It is appropriate to display a configuration dialog at this
        time.  If the conditions for the configuration of this step are complete
        then set:
            self._configured = True
        """
        dlg = ConfigureDialog(self._main_window)
        dlg.identifierOccursCount = self._identifierOccursCount
        dlg.setConfig(self._config)
        dlg.validate()
        dlg.setModal(True)

        if dlg.exec_():
            self._config = dlg.getConfig()

        self._configured = dlg.validate()
        self._configuredObserver()

    def getIdentifier(self):
        """
        The identifier is a string that must be unique within a workflow.
        """
        return self._config['identifier']

    def setIdentifier(self, identifier):
        """
        The framework will set the identifier for this step when it is loaded.
        """
        self._config['identifier'] = identifier

    def serialize(self):
        """
        Add code to serialize this step to string.  This method should
        implement the opposite of 'deserialize'.
        """
        return json.dumps(self._config, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def deserialize(self, string):
        """
        Add code to deserialize this step from string.  This method should
        implement the opposite of 'serialize'.

        :param string: JSON representation of the configuration in a string.
        """
        self._config.update(json.loads(string))

        d = ConfigureDialog()
        d.identifierOccursCount = self._identifierOccursCount
        d.setConfig(self._config)
        self._configured = d.validate()


