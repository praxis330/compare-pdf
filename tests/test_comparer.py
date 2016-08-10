import unittest
from mock import patch, call, Mock
from compare import PdfComparer, PdfToPngConverter
from PIL import Image


class BasePdfToPngConverterTest(unittest.TestCase):
  def setUp(self):
    self.threshold = 10
    self.baseline = "baseline_pdf"
    self.comparee = "comparee_pdf"
    self.temp_dir = "/temp_dir"


class InitTest(BasePdfToPngConverterTest):

  @patch('tempfile.mkdtemp', autospec=True)
  def test_it_should_create_a_temp_dir(self, mock_mkdtemp):
    mock_mkdtemp.return_value = self.temp_dir

    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)
    self.assertTrue(comparer.temp_dir, self.temp_dir)

  @patch.object(PdfToPngConverter, 'convert', autospec=True)
  def test_it_should_convert_each_document(self, mock_convert):
    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)

    calls = [call(comparer.baseline_conv), call(comparer.comparee_conv)]

    mock_convert.assert_has_calls(calls)
    self.assertEqual(mock_convert.call_count, 2)


class AreLengthsEqualTest(BasePdfToPngConverterTest):

  def _compare_lengths(self, baseline_paths, comparee_paths):
    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)
    comparer.baseline_paths = baseline_paths
    comparer.comparee_paths = comparee_paths

    return comparer.are_lengths_equal()

  @patch.object(PdfToPngConverter, 'convert', autospec=True)
  def test_it_should_return_True_if_lengths_are_the_same(self, mock_convert):
    baseline_paths = ['baseline_page_one', 'baseline_page_two']
    comparee_paths = ['comparee_page_one', 'comparee_page_two'] 

    lengths_equal = self._compare_lengths(baseline_paths, comparee_paths)

    self.assertTrue(lengths_equal)

  @patch.object(PdfToPngConverter, 'convert', autospec=True)
  def test_it_should_return_True_if_lengths_are_the_same(self, mock_convert):
    baseline_paths = ['baseline_page_one', 'baseline_page_two']
    comparee_paths = ['comparee_page_one'] 

    lengths_equal = self._compare_lengths(baseline_paths, comparee_paths)

    self.assertFalse(lengths_equal)


class AreImagesEqualTest(BasePdfToPngConverterTest):

  @patch.object(Image, 'open', autospec=True)
  @patch.object(PdfComparer, '_root_mean_square_error', autospec=True)
  @patch.object(PdfToPngConverter, 'convert', autospec=True)
  def test_it_should_return_false_if_the_error_is_over_the_threshold(self, mock_convert, mock_rms, mock_open):
    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)
    comparer.baseline_paths = ['baseline_page_one', 'baseline_page_two']
    comparer.comparee_paths = ['comparee_page_one', 'comparee_page_two']

    mock_rms.return_value = self.threshold + 20

    self.assertFalse(comparer.are_images_equal())

  @patch.object(Image, 'open', autospec=True)
  @patch.object(PdfComparer, '_root_mean_square_error', autospec=True)
  @patch.object(PdfToPngConverter, 'convert', autospec=True)
  def test_it_should_return_true_if_the_error_is_under_the_threshold(self, mock_convert, mock_rms, mock_open):
    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)
    comparer.baseline_paths = ['baseline_page_one', 'baseline_page_two']
    comparer.comparee_paths = ['comparee_page_one', 'comparee_page_two']

    mock_rms.return_value = self.threshold - 5

    self.assertTrue(comparer.are_images_equal())

class CompareTest(BasePdfToPngConverterTest):

  @patch.object(PdfComparer, '_tear_down_temp_dir', autospec=True)
  @patch.object(PdfComparer, 'are_lengths_equal', autospec=True)
  @patch.object(PdfComparer, 'are_images_equal', autospec=True)
  def test_it_should_tear_down_the_temp_dir_when_calling_compare(self, mock_images_equal, mock_lengths_equal, mock_tear_down):
    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)
    
    comparer.compare()

    mock_tear_down.assert_called_once_with(comparer)

  @patch.object(PdfComparer, '_tear_down_temp_dir', autospec=True)
  @patch.object(PdfComparer, 'are_lengths_equal', autospec=True)
  @patch.object(PdfComparer, 'are_images_equal', autospec=True)
  def test_it_should_not_compare_images_if_lengths_are_not_equal(self, mock_images_equal, mock_lengths_equal, mock_tear_down):
    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)
    mock_lengths_equal.return_value = False
    
    self.assertFalse(comparer.compare())
    self.assertFalse(mock_images_equal.called)

  @patch.object(PdfComparer, '_tear_down_temp_dir', autospec=True)
  @patch.object(PdfComparer, 'are_lengths_equal', autospec=True)
  @patch.object(PdfComparer, 'are_images_equal', autospec=True)
  def test_it_should_not_compare_images_if_lengths_are_not_equal(self, mock_images_equal, mock_lengths_equal, mock_tear_down):
    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)
    mock_lengths_equal.return_value = True
    mock_images_equal.return_value = False
    
    self.assertFalse(comparer.compare())
    mock_images_equal.assert_called_once_with(comparer)

  @patch.object(PdfComparer, '_tear_down_temp_dir', autospec=True)
  @patch.object(PdfComparer, 'are_lengths_equal', autospec=True)
  @patch.object(PdfComparer, 'are_images_equal', autospec=True)
  def test_it_return_true_if_images_and_lengths_are_equal(self, mock_images_equal, mock_lengths_equal, mock_tear_down):
    comparer = PdfComparer(self.baseline, self.comparee, self.threshold)
    mock_lengths_equal.return_value = True
    mock_images_equal.return_value = True
    
    self.assertTrue(comparer.compare())
    mock_images_equal.assert_called_once_with(comparer)
