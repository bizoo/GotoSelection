import sublime_plugin
import os.path
import re

RE_STRING_DELIMITER = re.compile('\\W')


class GotoSelectionCommand(sublime_plugin.WindowCommand):

	def run(self, scope=""):
		view = self.window.active_view()
		selection = view.sel()
		if selection and len(selection) == 1:
			selection = selection[0]

			text = self.get_text(view, selection)
			text = self.filter_text(text)
			text = scope + text

			self.window.run_command("show_overlay", {"overlay": "goto", "text": text})
			# In ST2 2187, show_overlay with a text parameter doesn't select an item, you have to navigate down arrow to select the first item.
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
		return view.substr(region)

	def filter_text(self, text):
		return text


class GotoSelectionFileCommand(GotoSelectionCommand):

	def get_text(self, view, selection):
		if selection.empty():
			# if cursor is in a string, get the content without string delimiter
			if view.score_selector(selection.begin(), "string") > 0:
				region = view.extract_scope(selection.begin())
				text = view.substr(region)
				while len(text) > 1:
					# remove the first and last char. if they are the same (string delimiter)
					if text[0] == text[-1] and RE_STRING_DELIMITER.search(text[0]):
						text = text[1:-1]
					else:
						break
				return text
			# As 2219, doesn't work. You can't specify both file and item name ("@").
			# elif view.score_selector(selection.begin(), "source.plsql.oracle") > 0:
			# 	region = view.word(selection)
			# 	package = view.substr(region)
			# 	print package, view.substr(region.end())
			# 	if view.substr(region.end()) == ".":
			# 		method = view.substr(view.word(region.end() + 1))
			# 	else:
			# 		method = None
			# 	return package + "@" + method
		return super(GotoSelectionFileCommand, self).get_text(view, selection)

	def filter_text(self, text):
		text = super(GotoSelectionFileCommand, self).filter_text(text)
		# filter begining path until last ..
		path, filename = os.path.split(text)
		path = path.rpartition("..")[2]
		path = path.rpartition(".")[2]
		return os.path.join(path, filename)
