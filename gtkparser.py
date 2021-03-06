#!/usr/bin/env python2.6
# ====
# A package for parsing xml files and converting them into a gtk widget dom tree
# ====
# Example:
#		win = gtk.Window()
#   ...
# 	Parser(win, 'res/layouts/main.xml').parse()
#   win.show()
#   gtk.main()
#
import sys
from xml.etree.ElementTree import parse as xmlparse
import pygtk
pygtk.require('2.0')
import gtk
import time

## // Constants //

DEF_HOMEOGENEOUS = False
DEF_SPACING = 0
DEF_EXPAND = False
DEF_FILL = False
DEF_PADDING = 0

## // Attributes //

def timerdef(func):
	""" an attribute to time a method """
	def wrapper(*arg):
		start = time.time()
		res = func(*arg)
		end = time.time()
		print "%s took %0.3f ms" % (func.func_name, (end-start)*1000.0)
		return res
	return wrapper

## // Errors //

class InvalidParentError(Exception):
	""" when a widget tries to be added to a parent widget, which doesn't respond to .pack_start or .add """
	def __init__(self, parent, child):
		self.parent = parent
		self.child = child

	def __str__(self):
		return "Parent did not have packing attrs.\nParent: " + repr(self.parent) + "\nChild: " + repr(self.child)


class WidgetCannotHaveChildError(Exception):
	def __init__(self, parent, child):
		self.parent = parent
		self.child = child

	def __str__(self):
		return "Parent %s is not able to have a child of %s" % (repr(self.parent), repr(self.child))


class UnknownWidgetError(Exception):
	""" a widget exists in the xml that isn't recognized/supported """
	def __init__(self, xmlelem):
		self.xmlelem = xmlelem

	def __str__(self):
		return "Unknown widget in xml. " + repr(self.xmlelem)


class CouldNotCreateWidgetError(Exception):
	""" could not create widget due to some unknown reason, give the user the xml blob and let them figure it out!! """
	def __init__(self, xmlelem):
		self.xmlelem = xmlelem

	def __str__(self):
		return "Could not create gtk widget from xml element. " + repr(self.xmlelem)


## // Parser //

class Parser:
	def __init__(self, gtkwin, path, debug=False):
		""" Parser(gtkwin, path) 
				@gtkwin - The gtk.Window which will contain the widgets parsed from the xml file at @path
				@path - The file path of the xml file containing the widget definition 
				@debug - Write debug info to stdout if True
				"""
		self.gtkwin = gtkwin
		self.path = path
		self.debug = debug

	@timerdef
	def parse(self):
		""" parse the xml in self.path and return the gtk translation """
		dom = xmlparse(self.path)
		root = dom.getroot()
		self.add_element(root, self.gtkwin) # start the recursive parsing 
	
	def add_element(self, xmlelem, gtkparent):
		""" add_element(xmleleme, gtkparent)
			  @xmlelem - the xml element to parse
				@gtkparent - the gtk widget to push this widget into
				"""
		# first convert this widget
		print ":: found element %s" % xmlelem.tag
		gtkwidget, expand, fill, padding, canHaveChildren  = self.convert_element(xmlelem)
		if gtkwidget:
			gtkwidget.show()
			if hasattr(gtkparent, 'pack_start'):
				gtkparent.pack_start(gtkwidget, expand, fill, padding)
			elif hasattr(gtkparent, 'add'):
				gtkparent.add(gtkwidget)
			else:
				raise InvalidParent(gtkparent, gtkwidget)
		else:
			raise CouldNotCreateWidgetError(xmlelem)
		# then do it's children
		for child in xmlelem.getchildren():
			if not canHaveChildren:
				raise WidgetCannotHaveChildrenError(xmlelem, child)
			self.add_element(child, gtkwidget)

	def convert_element(self, xmlelem):
		""" convert_element(xmlelem)
				@xmlelem - the xml representation of an element
				Returns:
					@gtkwidget - the gtk translation
					@expand - if the widget should be added with expand
					@fill - if the widget should be added with fill
					@padding - if the widget should be added with padding
				"""
		# supported widgets
		tag = xmlelem.tag
		if tag == "VBox":
			return self.convert_vbox(xmlelem)
		elif tag == "HBox":
			return self.convert_hbox(xmlelem)
		elif tag == "Button":
			return self.convert_button(xmlelem)
		else:
			raise UnknownWidgetError(xmlelem)

	def get_efp(self, node):
		""" get expand, fill, and padding """
		expand = node.attrib['expand']=='true' if 'expand' in node.attrib else DEF_EXPAND
		fill = node.attrib['fill']=='true' if 'fill' in node.attrib else DEF_FILL
		padding = node.attrib['padding']=='true' if 'padding' in node.attrib else DEF_PADDING
		return expand, fill, padding

	def set_widget_props(self, node, gtkwidget):
		""" set_widget_props(node, gtkwidget)
				@node - xml node containing the element
				@gtkwidget - the gtk widget
				grab widget properties and set them on the widget 
				"""
		if 'size' in node.attrib:
				size = node.attrib['size'].split('x')
				gtkwidget.set_size_request(int(size[0]), (int(size[1]) if len(size) > 1 else -1))
				print "set size-request = %s" % repr(size)
		if 'background' in node.attrib:
				background = node.attrib['background']
				gtkwidget.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse(background))
				print "set bg = %s" % repr(background)
		if 'foreground' in node.attrib:
				foreground = node.attrib['foreground']
				gtkwidget.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse(foreground))
				print "set fg = %s" % repr(foreground)

	def convert_vbox(self, node):
		homogeneous = node.attrib['homogeneous'] == 'true' if 'homogeneous' in node.attrib else DEF_HOMEOGENEOUS 
		spacing = int(node.attrib['spacing']) if 'spacing' in node.attrib else DEF_SPACING
		e, f, p = self.get_efp(node)
		widget = gtk.VBox(homogeneous, spacing)
		self.set_widget_props(node, widget)
		if self.debug:
			print "vbox: homogeneous=%s, spacing=%d, expand=%s, fill=%s, padding=%d" % (homogeneous, spacing, e, f, p)
		return widget, e, f, p, True

	def convert_hbox(self, node):
		homogeneous = node.attrib['homogeneous'] == 'true' if 'homogeneous' in node.attrib else DEF_HOMEOGENEOUS 
		spacing = int(node.attrib['spacing']) if 'spacing' in node.attrib else DEF_SPACING
		e, f, p = self.get_efp(node)
		widget = gtk.HBox(homogeneous, spacing)
		self.set_widget_props(node, widget)
		if self.debug:
			print "hbox: homogeneous=%s, spacing=%d, expand=%s, fill=%s, padding=%d" % (homogeneous, spacing, e, f, p)
		return widget, e, f, p, True

	def convert_button(self, node):
		label = node.attrib['text'] if 'text' in node.attrib else ''
		stock = node.attrib['stock'] if 'stock' in node.attrib else None
		e, f, p = self.get_efp(node)
		widget = gtk.Button(label, stock)
		self.set_widget_props(node, widget)
		if self.debug:
			print "button: label=%s, stock=%s, expand=%s, fill=%s, padding=%d" % (label, stock, e, f, p)
		return widget, e, f, p, False


## // Command Entry Point //

def harness_quit(widget, data=None):
	print "test quitting"
	gtk.main_quit()

if __name__ == "__main__":
	win = gtk.Window()
	win.set_title('Test Harness Window')
	win.connect("destroy", harness_quit)
	win.resize(600, 350)
	Parser(win, sys.argv[1], debug=True).parse()
	win.show()
	gtk.main()
