import tempfile
import subprocess
import os
import logging
import math
import shutil
from PIL import Image, ImageChops

logger = logging.getLogger('compare-pdf-util')

THRESHOLD = 10



class PdfComparer(object):
  def __init__(self, baseline, comparee, threshold):
    self.logger = logger

    self.temp_dir = tempfile.mkdtemp()

    self.baseline_conv = PdfToPngConverter(baseline, self.temp_dir)
    self.baseline_paths = self.baseline_conv.convert()

    self.comparee_conv = PdfToPngConverter(comparee, self.temp_dir)
    self.comparee_paths = self.comparee_conv.convert()

    self.threshold = threshold

  def compare(self):
    self.lengths_equal = self.are_lengths_equal()

    self.images_equal = True
    if self.lengths_equal:
      self.images_equal = self.are_images_equal()

    self._tear_down_temp_dir()

    return self.lengths_equal and self.images_equal

  def are_lengths_equal(self):
    if len(self.baseline_paths) != len(self.comparee_paths):
      return False
    return True

  def are_images_equal(self):
    for comparison_pair in zip(self.baseline_paths, self.comparee_paths):
      baseline_path, comparee_path = comparison_pair

      baseline_img = Image.open(baseline_path)
      comparee_img = Image.open(comparee_path)

      rms_error = self._root_mean_square_error(baseline_img, comparee_img)

      if rms_error > self.threshold:
        return False

    return True

  def _root_mean_square_error(self, baseline_img, comparee_img):
    diff = ImageChops.difference(
      baseline_img,
      comparee_img
    )

    histogram = diff.histogram()

    squares = (val * ((idx%256)**2) for idx, val in enumerate(histogram))
    sum_of_squares = sum(squares)

    baseline_x, baseline_y = baseline_img.size
    root_mean_square_error = math.sqrt(sum_of_squares/float(baseline_x * baseline_y))

    return root_mean_square_error

  def _tear_down_temp_dir(self):
    shutil.rmtree(self.temp_dir)


class PdfToPngConverter(object):
  def __init__(self, path, temp_dir):
    self.logger = logger
    self.path = path
    self.temp_dir = self._create_dir(temp_dir)

  def _create_dir(self, temp_dir):
    dir_path = os.path.join(temp_dir, self._get_filename())
    if not os.path.exists(dir_path):
      os.makedirs(dir_path)
    return dir_path

  def _get_filename(self):
    filename, _ = os.path.splitext(os.path.basename(self.path))
    return filename

  def _get_page_filename(self):
    return "{temp_dir}/{filename}_%03d.png".format(
      temp_dir=self.temp_dir,
      filename=self._get_filename())

  def _get_page_filepaths(self):
    filepaths = sorted(os.listdir(self.temp_dir))
    absolute_filepaths = [os.path.join(self.temp_dir, path) for path in filepaths]
    return absolute_filepaths

  def _convert(self):
    args = [
      'gs',
      '-sDEVICE=pngalpha',
      '-o',
      self._get_page_filename(),
      '-r300',
      self.path
    ]

    subprocess.check_output(args)

  def convert(self):
    try:
      self._convert()
      return self._get_page_filepaths()
    except subprocess.CalledProcessError:
      self.logger.error('Exception running ghostscript')

if __name__ == "__main__":
  comparer = PdfComparer('sample.pdf', 'sample_three.pdf', THRESHOLD)
  print comparer.compare()