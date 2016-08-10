import unittest
from mock import patch, Mock
import subprocess
from compare import PdfToPngConverter


class BasePdfToPngConverterTest(unittest.TestCase):
  def setUp(self):
    self.path = "path_to_pdf"
    self.temp_dir = "temp_dir"

    self.converter = PdfToPngConverter(self.path, self.temp_dir)


class InitTest(BasePdfToPngConverterTest):

  def test_it_should_create_the_converter_with_the_given_path(self):
    self.assertEqual(self.converter.path, self.path)

  @patch.object(PdfToPngConverter, '_create_dir', autospec=True)
  def test_it_should_create_the_converter_with_the_tempdir(self, mock_create_dir):
    mock_create_dir.return_value = 'temp_dir/path_to_pdf'
    self.assertEqual(self.converter.temp_dir, 'temp_dir/path_to_pdf')


class createDirTest(BasePdfToPngConverterTest):

  @patch.object(PdfToPngConverter, '_get_filename', autospec=True)
  @patch('os.makedirs', autospec=True)
  def test_it_should_use_the_filename_to_create_a_dir_within_temp_dir(self, mock_makedirs, mock_get_filename):
    dir_path = 'temp_dir/file_name'
    mock_get_filename.return_value = 'file_name'

    path = self.converter._create_dir(self.temp_dir)
    mock_makedirs.assert_called_once_with(dir_path)
    self.assertEqual(path, dir_path)


class GetFilenameTest(BasePdfToPngConverterTest):

  def test_it_should_extract_the_filename_from_the_page(self):
    self.converter.path = '/code/path_to_pdf.pdf'
    self.assertEqual(self.converter._get_filename(), "path_to_pdf")

  def test_it_should_extract_the_filename_if_there_is_no_path(self):
    self.converter.path = 'path_to_pdf.pdf'
    self.assertEqual(self.converter._get_filename(), "path_to_pdf")


class GetPageFilenameTest(BasePdfToPngConverterTest):

  @patch.object(PdfToPngConverter, '_get_filename', autospec=True)
  def test_it_should_format_the_filename_using_tempdir(self, mock_get_filename):
    self.converter.temp_dir = 'temp_dir'
    mock_get_filename.return_value = 'some_file'
    self.assertEqual(self.converter._get_page_filename(), "temp_dir/some_file_%03d.png")


class GetPageFilepaths(BasePdfToPngConverterTest):

  def setUp(self):
    super(GetPageFilepaths, self).setUp()
    self.converter.temp_dir = 'temp_dir'

  @patch('os.listdir', auto_spec=True)
  def test_it_should_return_a_list_of_file_paths_in_the_temp_dir(self, mock_walk):
    mock_walk.return_value = ['page_one', 'page_two']
    self.assertEqual(self.converter._get_page_filepaths(), ['temp_dir/page_one', 'temp_dir/page_two'])

  @patch('os.listdir', autospec=True)
  def test_it_should_return_a_the_list_of_file_paths_in_sorted_order(self, mock_walk):
    mock_walk.return_value = ['page_004.png', 'page_001.png', 'page_003.png']
    self.assertEqual(self.converter._get_page_filepaths(), ['temp_dir/page_001.png', 'temp_dir/page_003.png', 'temp_dir/page_004.png'])


class convertTest(BasePdfToPngConverterTest):

  @patch.object(PdfToPngConverter, '_get_page_filename', autospec=True)
  @patch('subprocess.check_output', autospec=True)
  def test_it_should_call_gs_with_the_path_of_the_given_file(self, mock_check_output, mock_get_page_filename):
    mock_get_page_filename.return_value = "page_filename"
    self.converter._convert()
    mock_check_output.assert_called_with(['gs', '-sDEVICE=pngalpha', '-o', 'page_filename', '-r300', 'path_to_pdf'])


class ConvertTest(BasePdfToPngConverterTest):

  @patch.object(PdfToPngConverter, '_convert', autospec=True)
  @patch.object(PdfToPngConverter, '_get_page_filepaths', autospec=True)
  def test_it_should_return_the_paths_to_the_split_pdf(self, mock_page_filepaths, mock_convert):
    mock_page_filepaths.return_value = ['page_one', 'page_two']
    pages = self.converter.convert()
    self.assertEqual(pages, ['page_one', 'page_two'])
    mock_convert.assert_called_once_with(self.converter)

  @patch.object(PdfToPngConverter, '_convert', autospec=True)
  def test_it_should_log_error_if_ghostscript_raises_an_exception(self, mock_convert):
    mock_convert.side_effect = subprocess.CalledProcessError(1, "exception", "exception")
    self.converter.logger.error = Mock()
    self.converter.convert()
    self.converter.logger.error.assert_called_once_with('Exception running ghostscript')
