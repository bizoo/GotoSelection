import sublime_plugin
import os.path
import re

RE_STRING_DELIMITER = re.compile('\\W')


class GotoSelectionCommand(sublime_plugin.WindowCommand):

	def run(self, scope="", prefix="", postfix="", **kwargs):
		self.prefix = prefix
		self.postfix = postfix
		view = self.window.active_view()
		selection = view.sel()
		if selection and len(selection) == 1:
			selection = selection[0]

			text = self.get_text(view, selection)
			if text is None:
				return
			text = scope + text

			self.window.run_command("show_overlay", {"overlay": "goto", "text": text})
			# In ST2 2187, show_overlay with a text parameter doesn't select an item, you have to hit down arrow to select the first item.
			# So there is no more issue with TRANSIENT view.
			# Workaround ST2 bug (2170):
			# When a file open in TRANSIENT mode with the first call to show_overlay, the overlay is automaticaly closed (or become invisible ?).
			# If the file is already opened, it works.
			# The two subsequent call to show_overlay reopen the overlay panel.
			# if view.window():
			# 	view.window().run_command("show_overlay", {"overlay": "goto"})
			# 	view.window().run_command("show_overlay", {"overlay": "goto", "text": text})

	def get_text(self, view, selection):
		if selection.empty():
			region = view.word(selection)
		else:
			region = selection
		return self.prefix + self.filter_text(view.substr(region)) + self.postfix

	def filter_text(self, text):
		return text


class GotoSelectionFileCommand(GotoSelectionCommand):

	def run(self, extension="", **kwargs):
		self.extension = extension
		super().run(**kwargs)

	def try_open_file(self, filename):
		if os.path.exists(filename):
			self.window.open_file(filename)
			return True

	def get_text(self, view, selection):
		# get current view path
		if view.file_name():
			filename = view.file_name()
			viewpath, _ = os.path.split(filename)
		else:
			filename = ""
			viewpath = ""
		if selection.empty():
			# if cursor is in a string, get the content without string delimiter
			# dont't add prefix, postfix and extension strings
			if view.score_selector(selection.begin(), "string") > 0:
				region = view.extract_scope(selection.begin())
				text = view.substr(region)
				while len(text) > 1:
					# remove the first and last char. if they are the same (string delimiter)
					if text[0] == text[-1] and RE_STRING_DELIMITER.search(text[0]):
						text = text[1:-1]
					else:
						break
				# Try if string is an absolute path, or a relative (to the current file path) path
				testpath = os.path.normpath(os.path.join(viewpath, text))
				if testpath.lower() != view.file_name().lower() and self.try_open_file(testpath):
					# It's an existing file, stop here
					return

		# try current directory
		text = super().get_text(view, selection)
		if not text.lower().endswith(self.extension.lower()):
			text = text + self.extension
		testpath = os.path.normpath(os.path.join(viewpath, text))
		if testpath.lower() != filename.lower() and self.try_open_file(testpath):
			# It's an existing file, stop here
			return

		return self._filter_text_for_st(text)

	def _filter_text_for_st(self, text):
		# filter begining path until last ..
		path, filename = os.path.split(text)
		path = path.rpartition("..")[2]
		path = path.rpartition(".")[2]
		return os.path.join(path, filename)
