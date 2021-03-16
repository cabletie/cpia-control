###########################################################################
#
# $Id: cpia_control.py,v 1.11 2002/12/17 07:37:45 duncan_haldane Exp $
#
# Copyright (C) 2000, Peter Pregler (Peter_Pregler@email.com)
#                     
###########################################################################
#
#  $Revision: 1.11 $
#  $Date: 2002/12/17 07:37:45 $
#  $Author: duncan_haldane $
#  Created by: Peter Pregler.
#
###########################################################################
#
# Description:
#    All the GUI stuff.
#
###########################################################################

###########################################################################
#
# imported modules
#
###########################################################################

## threading does not work with Gtkinter - so mark what we are using
try:
    # it gets more complicated - additional mechanism to find gtk1.2
    try:
        import pygtk
#        pygtk.require('>1.2')
    except ImportError:
        pass
    from gtk import *
    have_gtk=1
except ImportError:
    from Gtkinter import *
    have_gtk=0

import GtkExtra
import thread
import time
import math
import sys

import libcpia

###########################################################################
#
# global variables
#
###########################################################################

cpia_control_version='0.5.1'
cpia_debug=0

camera=''
callback_object={}
callback_type={}

####################################################################
#
# unimplemented keys:
# (remove from this list and from keys_to_ignore if/when control is
# implemented for them here) 
#
#         stream_start_line,
#         red_comp, green1_comp, green2_comp, blue_comp,
#         apcor_gain1, apcore_gain2, apcor_gain4, apcor_gain8
#         vl_offset_gain1, vl_offset_gain2, vl_offset_gain3, vl_offset_gain4
#         allowable_overexposure,
#         hysteresis, threshold_max, small_step, large_step,
#         decimation_hysteresis, fr_diff_step_thresh, q_diff_step_thresh
#         decimation_thresh_mod
#
####################################################################

keys_to_ignore=["stream_start_line",
                "red_comp", "green1_comp", "green2_comp", "blue_comp",
                "apcor_gain1", "apcore_gain2", "apcor_gain4", "apcor_gain8",
                "vl_offset_gain1", "vl_offset_gain2", "vl_offset_gain3",
                "vl_offset_gain4",
                "allowable_overexposure",
                "hysteresis", "threshold_max", "small_step", "large_step",
                "decimation_hysteresis", "fr_diff_step_thresh",
                "q_diff_step_thresh","decimation_thresh_mod"]

######################################################################
#
# generic set/unset callbacks
#
######################################################################

def set_on_off(button):
    if button.active:
        camera.set_value(button.get_name(),'off')
    else:
        camera.set_value(button.get_name(),'on')
            
def set_auto_manual(button):
    if button.active:
        camera.set_value(button.get_name(),'manual')
    else:
        camera.set_value(button.get_name(),'auto')

######################################################################
def register_callback(key, type, object):
    callback_object[key]=object
    callback_type[key]=type
    return

def execute_callback(key):
    if key in keys_to_ignore:
        return
    try:
        type=callback_type[key]
        object=callback_object[key]
        #print key+' - '+type+' callback'


        if type == 'adjustment':
            #print 'adjustment: '+key
            value=int(camera.get_value(key))
            object.set_value(value)
        if type == 'check_button':
            #print 'check_button: '+key
            value=camera.get_value(key)
            if value=='auto' or value=='on':
                object.set_active(TRUE)
            else:
                object.set_active(FALSE)
        if type == 'radio_button':
            #print 'radio_button: '+key
            value=camera.get_value(key)
            index=0
            if value=='auto' or value=='quality' or value=='60':
                index=1
            if value=='manual':
                index=2
            object=object[index]
            object.set_active(TRUE)
        if type == 'radio_menu':
            #print 'radio_menu: '+key
            value=camera.get_value(key)
            values=['30.000','25.000','15.000','12.500','7.500','6.250','3.750']
            try:
                index=values.index(value)
            except:
                values=['1','2','4','8']
                index=values.index(value)
            optionmenu=object[-1]       # UGLY!
            optionmenu.set_history(index)
            object=object[index]
            object.set_active(TRUE)
            
    except KeyError:
        print key+' - no callback registered'
        pass
    return
    

######################################################################
#
# generic new widgets
#
######################################################################

def add_slider(sliders, frame_text, action, action_text):
    frame = GtkFrame(frame_text)
    sliders.pack_start(frame)
    frame.show()

    values=camera.get_values(action_text)
    value=int(values[0])
    min_val=int(values[1])
    max_val=int(values[2])+1    
    adjustment = GtkAdjustment(value, min_val, max_val, 1, 1, 1)
    adjustment.connect("value_changed", action)
    register_callback(action_text, 'adjustment', adjustment)
    scale = GtkVScale(adjustment)
    scale.set_usize(30, 100)
    scale.set_update_policy(UPDATE_DELAYED)
    scale.set_digits(0)
    scale.set_draw_value(TRUE)
    frame.add(scale)
    scale.show()


def create_radio_menu(optionmenu, menu, key, values, active, unit):
    group=None
    index=0
    active_index=0
    objects=[]
    if key=='sensor_fps':
        action=exposure_set_fps
    elif key=='max_gain':
        action=exposure_set_max_gain
    elif key=='gain':
        action=exposure_set_gain
    for item in values:
        menu_item = GtkRadioMenuItem(group, unit+": "+item)
        menu_item.connect("activate", action)
        menu.append(menu_item)
        objects.append(menu_item)
        menu_item.set_name(item)
        menu_item.show()
        if active != "" and float(active)==float(item):
            menu_item.set_active(TRUE);
            active_index=index
        group=menu_item
        index=index+1
    menu.set_active(active_index)
    objects.append(optionmenu)
    register_callback(key, 'radio_menu', objects)

######################################################################
#
# color_balance: red_gain blue_gain green_gain
#
######################################################################

def red_gain_set(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('red_gain',value)
    
def blue_gain_set(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('blue_gain',value)
    
def green_gain_set(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('green_gain',value)

def create_color_balance(notebook):

    # radio buttons | sliders
    label = GtkLabel("Color balance")
    all = GtkHBox()
    notebook.append_page(all, label)
    all.show()

    # control buttons : on/off
    left_row = GtkVBox()
    all.pack_start(left_row)
    left_row.show()

    button = GtkCheckButton("on/off")
    left_row.pack_start(button)
    if camera.get_value('color_balance_mode')=='auto':
        button.set_active(TRUE);
    button.set_name('color_balance_mode')
    button.connect("pressed", set_auto_manual)
    register_callback('color_balance_mode', 'check_button', button)
    button.show()

    # sliders: red/blue/green gain
    sliders = GtkHBox()
    all.pack_start(sliders)
    sliders.show()

    add_slider(sliders, "red gain", red_gain_set, "red_gain")
    add_slider(sliders, "blue gain", blue_gain_set, "blue_gain")
    add_slider(sliders, "green gain", green_gain_set, "green_gain")
    

######################################################################
#
# exposure: fine_exp coarse_exp sensor_fps gain max_gain exposure_mode 
#
######################################################################

def fine_exp(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('fine_exp',value)
    
def coarse_exp(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('coarse_exp',value)
    
def exposure_set_fps(button):
    if button.active:
        value=str(int(math.floor(float(button.get_name()))))
        camera.set_value('sensor_fps', value)
            
def exposure_set_gain(button):
    if button.active:
        camera.set_value('gain', button.get_name())
            
def exposure_set_max_gain(button):
    if button.active:
        camera.set_value('max_gain', button.get_name())
            
def create_exposure(notebook):
    
    # radio buttons | threshold sliders
    label = GtkLabel("Exposure")
    all = GtkHBox()
    notebook.append_page(all, label)
    all.show()

    # control buttons : exposure_mode sensor fps
    left_row = GtkVBox()
    all.pack_start(left_row)
    left_row.show()

    button = GtkCheckButton("auto/manual")
    left_row.pack_start(button)
    if camera.get_value('exposure_mode')=='auto':
        button.set_active(TRUE);
    button.set_name('exposure_mode')
    button.connect("pressed", set_auto_manual)
    register_callback('exposure_mode', 'check_button', button)
    button.show()

    # sensor fps
    optionmenu = GtkOptionMenu()
    radio = GtkMenu()
    value=camera.get_value('sensor_fps')
    values=['30','25','15','12.5','7.5','6.25','3.75']
    create_radio_menu(optionmenu, radio, 'sensor_fps', values, value, 'fps')
    #create_radio_menu(radio, exposure_set_fps, values, value, 'fps')
    
    optionmenu.set_menu(radio)
    left_row.pack_start(optionmenu)
    optionmenu.show()

    # max gain
    optionmenu = GtkOptionMenu()
    radio = GtkMenu()
    value=camera.get_value('max_gain')
    values=['1','2','4','8']
    create_radio_menu(optionmenu, radio, 'max_gain', values, value, 'max. gain')
    #create_radio_menu(radio, exposure_set_max_gain, values, value, 'max. gain')

    optionmenu.set_menu(radio)
    left_row.pack_start(optionmenu)
    optionmenu.show()
    
    # gain
    optionmenu = GtkOptionMenu()
    radio = GtkMenu()
    value=camera.get_value('gain')
    values=['1','2','4','8']
    create_radio_menu(optionmenu, radio, 'gain', values, value, 'gain')
    #create_radio_menu(radio, exposure_set_gain, values, value, 'max. gain')

    optionmenu.set_menu(radio)
    left_row.pack_start(optionmenu)
    optionmenu.show()

    # sliders : 
    sliders = GtkHBox()
    all.pack_start(sliders)
    sliders.show()

    add_slider(sliders, "fine", fine_exp, "fine_exp")
    add_slider(sliders, "coarse", coarse_exp, "coarse_exp")

######################################################################
#
# filter: centre_weight flicker_control mains_frequency
#
######################################################################

def exposure_set_mains(button):
    camera.set_value('mains_frequency', button.get_name())
            
def create_filter(notebook):

    # radio buttons | threshold sliders
    label = GtkLabel("Filter")
    all = GtkHBox()
    notebook.append_page(all, label)
    all.show()

    # control buttons : center weight
    left_row = GtkVBox()
    all.pack_start(left_row)
    left_row.show()

    button = GtkCheckButton("Center weight")
    left_row.pack_start(button)
    if camera.get_value('centre_weight')=='on':
        button.set_active(TRUE);
    button.set_name('centre_weight')
    button.connect("pressed", set_on_off)
    register_callback('centre_weight', 'check_button', button)
    button.show()

    # flicker control / mains
    frame = GtkFrame('Flicker control')
    all.pack_start(frame)
    frame.show()

    buttons = GtkVBox()
    frame.add(buttons)
    buttons.show()

    button = GtkCheckButton("on/off")
    buttons.pack_start(button)
    if camera.get_value('flicker_control')=='on':
        button.set_active(TRUE);
    button.set_name('flicker_control')
    button.connect("pressed", set_on_off)
    register_callback('flicker_control', 'check_button', button)
    button.show()

    button1 = GtkRadioButton(None, "50 Hz")
    button1.connect("pressed", exposure_set_mains)
    buttons.pack_start(button1)
    button1.set_name('50')
    button1.show()
    
    button2 = GtkRadioButton(button1, "60 Hz")
    button2.connect("pressed", exposure_set_mains)
    buttons.pack_start(button2)
    if camera.get_value('mains_frequency')=='60':
        button2.set_active(TRUE);
    button2.set_name('60')
    button2.show()

    register_callback('mains_frequency', 'radio_button', [button1, button2] )

######################################################################
#
# picture settings: saturation brightness contrast
#
######################################################################

def brightness_set(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('brightness',value)

def saturation_set(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('saturation',value)

    # contrast is a multiple of 8
def contrast_set(adjustment):
    new_value=int(adjustment.value)
    new_value=(new_value+3)/8
    value=str(8*new_value)
    camera.set_value('contrast',value)
    
def create_picture(notebook):

    label = GtkLabel("Picture")

    # brightness saturation (color) contrast
    all = GtkHBox()
    all.show()
    notebook.append_page(all, label)
    
    # brightness
    frame = GtkFrame("Brightness")
    all.pack_start(frame)
    frame.show()
    
    #[value, min_value, max_value, def_value]=camera.get_values('brightness')
    #adjustment = GtkAdjustment(int(value), int(min_value), int(max_value),
    #                           1, 1, 1)
    values=camera.get_values('brightness')
    value=int(values[0])
    min_val=int(values[1])
    max_val=int(values[2])+1    
    adjustment = GtkAdjustment(value, min_val, max_val, 1, 1, 1)
    adjustment.connect("value_changed", brightness_set)
    register_callback('brightness', 'adjustment', adjustment)
    scale = GtkVScale(adjustment)
    scale.set_usize(30, 100)
    scale.set_update_policy(UPDATE_DELAYED)
    scale.set_digits(0)
    scale.set_draw_value(TRUE)
    frame.add(scale)
    scale.show()

    # color
    frame = GtkFrame("Color")
    all.pack_start(frame)
    frame.show()
    
    values=camera.get_values('saturation')
    value=int(values[0])
    min_val=int(values[1])
    max_val=int(values[2])+1    
    adjustment = GtkAdjustment(value, min_val, max_val, 1, 1, 1)
    adjustment.connect("value_changed", saturation_set)
    register_callback('saturation', 'adjustment', adjustment)
    scale = GtkVScale(adjustment)
    scale.set_usize(30, 100)
    scale.set_update_policy(UPDATE_DELAYED)
    scale.set_digits(0)
    scale.set_draw_value(TRUE)
    frame.add(scale)
    scale.show()

    # contrast
    frame = GtkFrame("Contrast")
    all.pack_start(frame)
    frame.show()

    #note this should be in steps of 8
    values=camera.get_values('contrast')
    value=int(values[0])
    min_val=int(values[1])
    max_val=int(values[2])+1    
    adjustment = GtkAdjustment(value, min_val, max_val, 1, 1, 1)
    adjustment.connect("value_changed", contrast_set)
    register_callback('contrast', 'adjustment', adjustment)
    scale = GtkVScale(adjustment)
    scale.set_usize(30, 100)
    scale.set_update_policy(UPDATE_DELAYED)
    scale.set_digits(0)
    scale.set_draw_value(TRUE)
    frame.add(scale)
    scale.show()

######################################################################
#
# compression control: compression_mode target_framerate target_quality
#                      y_threshold uv_threshold
#
######################################################################

def compression_set_mode(button):
    camera.set_value('compression_mode',button.get_name())
    
def compression_set_target(button):
    camera.set_value('compression_target',button.get_name())
    
def compression_set_target_framerate(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('target_framerate',value)
    
def compression_set_target_quality(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('target_quality',value)
    
def compression_set_y(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('y_threshold',value)
    
def compression_set_uv(adjustment):
    value=str(int(adjustment.value))
    camera.set_value('uv_threshold',value)
    
def create_compression(notebook):

    label = GtkLabel("Compression")

    all = GtkHBox()
    all.show()
    notebook.append_page(all, label)
    
    frame = GtkFrame("Mode")
    all.pack_start(frame)
    frame.show()

    # mode control: radio buttons | threshold sliders
    mode = GtkHBox()
    frame.add(mode)
    mode.show()

    # compression radio button
    comp = GtkVBox(spacing=10)
    mode.add(comp)
    comp.show()

    # set to correct value
    value=camera.get_value('compression_mode')
    
    # compression none
    button1 = GtkRadioButton(None, "none")
    comp.pack_start(button1)
    button1.set_name('none')
    button1.connect("pressed", compression_set_mode)
    button1.show()

    # compression auto
    button2 = GtkRadioButton(button1, "auto")
    comp.pack_start(button2)
    button2.set_name('auto')
    if value=='auto':
        button2.set_active(TRUE)
    button2.connect("pressed", compression_set_mode)
    button2.show()

    # compression manual
    button3 = GtkRadioButton(button2, "manual")
    comp.pack_start(button3)
    button3.set_name('manual')
    if value=='manual':
        button3.set_active(TRUE)
    button3.connect("pressed", compression_set_mode)
    button3.show()

    register_callback('compression_mode', 'radio_button',
                      [button1, button2, button3] )
    
    # y-threshold
    frame = GtkFrame("Y")
    mode.pack_start(frame)
    frame.show()
    
    values=camera.get_values('y_threshold')
    value=int(values[0])
    min_val=int(values[1])
    max_val=int(values[2])+1    
    adjustment = GtkAdjustment(value, min_val, max_val, 1, 1, 1)
    adjustment.connect("value_changed", compression_set_y)
    register_callback('y_threshold', 'adjustment', adjustment)
    scale = GtkVScale(adjustment)
    scale.set_usize(30, 100)
    scale.set_update_policy(UPDATE_DELAYED)
    scale.set_digits(0)
    scale.set_draw_value(TRUE)
    frame.add(scale)
    scale.show()

    # uy-threshold
    frame = GtkFrame("UV")
    mode.pack_start(frame)
    frame.show()

    values=camera.get_values('uv_threshold')
    value=int(values[0])
    min_val=int(values[1])
    max_val=int(values[2])+1    
    adjustment = GtkAdjustment(value, min_val, max_val, 1, 1, 1)
    adjustment.connect("value_changed", compression_set_uv)
    register_callback('uv_threshold', 'adjustment', adjustment)
    scale = GtkVScale(adjustment)
    scale.set_usize(30, 100)
    scale.set_update_policy(UPDATE_DELAYED)
    scale.set_digits(0)
    scale.set_draw_value(TRUE)
    frame.add(scale)
    scale.show()

    frame = GtkFrame("Target")
    #frame.set_border_width(5)
    all.pack_start(frame)
    frame.show()

    # target control: radio buttons | sliders
    mode = GtkHBox()
    frame.add(mode)
    mode.show()

    # compression radio button
    comp = GtkVBox(spacing=10)
    #comp.set_border_width(10)
    mode.add(comp)
    comp.show()

    # set to correct value
    value=camera.get_value('compression_target')
    
    # compression frame rate
    button1 = GtkRadioButton(None, "framerate")
    comp.pack_start(button1)
    if value=='framerate':
        button1.set_active(TRUE)
    button1.set_name('framerate')
    button1.connect("pressed", compression_set_target)
    button1.show()

    # compression quality
    button2 = GtkRadioButton(button1, "quality")
    comp.pack_start(button2)
    if value=='quality':
        button2.set_active(TRUE)
    button2.set_name('quality')
    button2.connect("pressed", compression_set_target)
    button2.show()

    register_callback('compression_target', 'radio_button', [button1, button2] )

    # target framerate
    frame = GtkFrame("FR")
    mode.pack_start(frame)
    frame.show()

    values=camera.get_values('target_framerate')
    value=int(values[0])
    min_val=int(values[1])
    max_val=int(values[2])+1    
    adjustment = GtkAdjustment(value, min_val, max_val, 1, 1, 1)
    adjustment.connect("value_changed", compression_set_target_framerate)
    register_callback('target_framerate', 'adjustment', adjustment)
    scale = GtkVScale(adjustment)
    scale.set_usize(30, 100)
    scale.set_update_policy(UPDATE_DELAYED)
    scale.set_digits(0)
    scale.set_draw_value(TRUE)
    frame.add(scale)
    scale.show()

    # target quality
    frame = GtkFrame("Q")
    mode.pack_start(frame)
    frame.show()

    values=camera.get_values('target_quality')
    value=int(values[0])
    min_val=int(values[1])
    max_val=int(values[2])+1    
    adjustment = GtkAdjustment(value, min_val, max_val, 1, 1, 1)
    adjustment.connect("value_changed", compression_set_target_quality)
    register_callback('target_quality', 'adjustment', adjustment)
    scale = GtkVScale(adjustment)
    scale.set_usize(30, 100)
    scale.set_update_policy(UPDATE_DELAYED)
    scale.set_digits(0)
    scale.set_draw_value(TRUE)
    frame.add(scale)
    scale.show()




######################################################################
#
# misc control
#
######################################################################

def misc_set_yuv_order(button):
    camera.set_value('yuv_order',button.get_name())
    
def misc_set_sub_sample(button):
    camera.set_value('sub_sample',button.get_name())
    
def misc_set_ecp_timing(button):
    camera.set_value('ecp_timing',button.get_name())
    
def misc_set_usb_alt(button):
    camera.set_value('usb_alt_setting',button.get_name())
    
def create_misc(notebook):

    # radio buttons | threshold sliders
    label = GtkLabel("Misc")
    all = GtkHBox()
    notebook.append_page(all, label)
    all.show()

    frame = GtkFrame("Decimation")
    all.pack_start(frame)
    frame.show()
    
    # mode control: radio buttons | threshold sliders
    mode = GtkHBox()
    frame.add(mode)
    mode.show()
        
    # compression radio button
    comp = GtkVBox(spacing=10)
    mode.add(comp)
    comp.show()

    button = GtkCheckButton("on/off")
    comp.pack_start(button)
    if camera.get_value('decimation_enable')=='on':
        button.set_active(TRUE);
    button.set_name('decimation_enable')
    button.connect("pressed", set_on_off)
    register_callback('decimation_enable', 'check_button', button)
    button.show()
        

    # the next keys are sometimes not present or are
    # not supported by older driver versions:
    keys_rw=camera.get_keys_rw()

    # ecp_timing radio button
    if "ecp_timing" in keys_rw:  
        frame = GtkFrame("ECP Timing")
        all.pack_start(frame)
        frame.show()
        
        mode = GtkHBox()
        frame.add(mode)
        mode.show()
        comp = GtkVBox(spacing=10)
        mode.add(comp)
        comp.show()
        
        # set to correct value
        value=camera.get_value('ecp_timing')
        
        # compression radio button
        comp = GtkVBox(spacing=10)
        mode.add(comp)
        comp.show()
        
        button1 = GtkRadioButton(None, "normal")
        comp.pack_start(button1)
        button1.set_name('normal')
        button1.connect("pressed", misc_set_ecp_timing)
        button1.show()
        button2 = GtkRadioButton(button1, "slow")
        comp.pack_start(button2)
        button2.set_name('slow')
        if value=='slow':
            button2.set_active(TRUE)
        button2.connect("pressed", misc_set_ecp_timing)
        button2.show()
            
        register_callback('ecp_timing', 'radio_button',
                              [button1, button2] )
            
    # usb_alt radio button
    if "usb_alt_setting" in keys_rw:  
        frame = GtkFrame("USB Packet Size")
        all.pack_start(frame)
        frame.show()
        
        mode = GtkHBox()
        frame.add(mode)
        mode.show()
        comp = GtkVBox(spacing=10)
        mode.add(comp)
        comp.show()
        
        # set to correct value
        value=camera.get_value('usb_alt_setting')
        
        # compression radio button
        comp = GtkVBox(spacing=10)
        mode.add(comp)
        comp.show()
        
        button1 = GtkRadioButton(None, "Alt 1 (448)")
        comp.pack_start(button1)
        button1.set_name('1')
        button1.connect("pressed", misc_set_usb_alt)
        button1.show()
        button2 = GtkRadioButton(button1, "Alt 2 (704)")
        comp.pack_start(button2)
        button2.set_name('2')
        if value=='2':
            button2.set_active(TRUE)
        button2.connect("pressed", misc_set_usb_alt)
        button2.show()
        button3 = GtkRadioButton(button2, "Alt 3 (960)")
        comp.pack_start(button3)
        button3.set_name('3')
        if value=='3':
            button3.set_active(TRUE)
        button3.connect("pressed", misc_set_usb_alt)
        button3.show()
            
        register_callback('usb_alt_setting', 'radio_button',
                              [button1, button2, button3] )

    # yuv order radio button
    if "yuv_order" in keys_rw:  
            
        frame = GtkFrame("YUV order")
        all.pack_start(frame)
        frame.show()
        
        mode = GtkHBox()
        frame.add(mode)
        mode.show()
        
        comp = GtkVBox(spacing=10)
        mode.add(comp)
        comp.show()
        
        # set to correct value
        value=camera.get_value('yuv_order')
        
        # compression radio button
        comp = GtkVBox(spacing=10)
        
        mode.add(comp)
        comp.show()
        
        # yuv order
        button1 = GtkRadioButton(None, "YUYV")
        comp.pack_start(button1)
        button1.set_name('YUYV')
        button1.connect("pressed", misc_set_yuv_order)
        button1.show()
        
        # YUV order UYVY
        button2 = GtkRadioButton(button1, "UYVY")
        comp.pack_start(button2)
        button2.set_name('UYVY')
        if value=='UYVY':
            button2.set_active(TRUE)
        button2.connect("pressed", misc_set_yuv_order)
        button2.show()
        
        register_callback('yuv_order', 'radio_button',
                          [button1, button2] )

    # yuv subsample radio button
    if "sub_sample" in keys_rw:  
        frame = GtkFrame("YUV subsample")
        all.pack_start(frame)
        frame.show()
        
        # mode control: radio buttons | threshold sliders
        mode = GtkHBox()
        frame.add(mode)
        mode.show()
        
        comp = GtkVBox(spacing=10)
        mode.add(comp)
        comp.show()
        
        # set to correct value
        value=camera.get_value('sub_sample')
        
        # compression radio button
        comp = GtkVBox(spacing=10)
        mode.add(comp)
        comp.show()
        button1 = GtkRadioButton(None, "422")
        comp.pack_start(button1)
        button1.set_name('422')
        button1.connect("pressed", misc_set_sub_sample)
        button1.show()
        button2 = GtkRadioButton(button1, "420")
        comp.pack_start(button2)
        button2.set_name('420')
        if value=='420':
            button2.set_active(TRUE)
        button2.connect("pressed", misc_set_sub_sample)
        button2.show()

        register_callback('sub_sample', 'radio_button',
                      [button1, button2] )



##########################

def create_lights(all):

    button = GtkCheckButton("Top light")
    all.add(button);
    if camera.get_value('toplight')=='on':
      button.set_active(TRUE)
    button.set_name('toplight')
    button.connect("pressed", set_on_off)
    register_callback('toplight', 'check_button', button)
    button.show()

    button = GtkCheckButton("Bottom light")
    all.add(button);
    if camera.get_value('bottomlight')=='on':
      button.set_active(TRUE)
    button.set_name('bottomlight')
    button.connect("pressed", set_on_off)
    register_callback('bottomlight', 'check_button', button)
    button.show()
   

######################################################################
#
# load/save dialog
#
######################################################################

def delete_event(win, event=None):
        win.hide()
        # don't destroy window -- just leave it hidden
        return TRUE

def do_save_state(_button):
    win = GtkFileSelection("Save to file:")
    win.connect("delete_event", delete_event)
    def file_selection_ok(_button, fs=win):
        fname=fs.get_filename()
        if camera.save(fname):
            text='Save to file '+fname+' failed!'
            GtkExtra.message_box("Save failed!", text, ("Close",))
        fs.hide()
    win.ok_button.connect("clicked", file_selection_ok)
    win.cancel_button.connect("clicked", win.hide)
    win.show()

def do_load_state(_button):
    win = GtkFileSelection("Load from file:")
    win.connect("delete_event", delete_event)
    def file_selection_ok(_button, fs=win):
        fname=fs.get_filename()
        try:
            camera.load(fname)
        except IOError:
            text='Load from file '+fname+' failed!'
            GtkExtra.message_box("Load failed!", text, ("Close",))
        else:
            fs.hide()
    win.ok_button.connect("clicked", file_selection_ok)
    win.cancel_button.connect("clicked", win.hide)
    win.show()

######################################################################
#
# menubar items
#
######################################################################

def create_file_menu():
    menu = GtkMenu()

    menuitem = GtkMenuItem("Load state")
    menu.append(menuitem)
    menuitem.connect("activate", do_load_state)
    menuitem.show()
    
    menuitem = GtkMenuItem("Save state")
    menu.append(menuitem)
    menuitem.connect("activate", do_save_state)
    menuitem.show()
    
    menuitem = GtkMenuItem("Quit")
    menu.append(menuitem)
    menuitem.connect("activate", do_exit)
    menuitem.show()

    return menu

def create_help_menu():
    menu = GtkMenu()
    menuitem = GtkMenuItem("About")
    menu.append(menuitem)
    menuitem.connect('activate', create_about)
    menuitem.show()
    return menu

def create_about(_button):
    v4l_version=camera.get_value('V4L Driver version')
    if v4l_version=='':
        v4l_version='unknown'
    cpia_version=camera.get_value('CPIA Version')
    cpia_pnpid=camera.get_value('CPIA PnP-ID')
    vp_version=camera.get_value('VP-Version')
    text="CPiA camera control program (Version:"+cpia_control_version+")"+\
          "\nV4l Driver version: "+v4l_version+\
"""
Detected Camera:
"""+\
    "CPIA Version: "+cpia_version+"\n"+\
    "CPIA Pn-PID: "+cpia_pnpid+"\n"+\
    "VP-Version: "+vp_version+"\n"+\
"""
See http://webcam.sourceforge.net/ for more details

Copyright(c) 1999/2000/2004 by
Peter Pregler (Peter_Pregler@email.com)
"""
    GtkExtra.message_box("About CPiA control", text, ("Close",))

######################################################################
#
# status
#
######################################################################

def create_status(box):
    # close button
    separator = GtkHSeparator()
    box.pack_start(separator, expand=FALSE)
    separator.show()
    box2 = GtkHBox(spacing=10)
    box.pack_start(box2, expand=FALSE)
    box2.show()

    is_microscope=camera.get_value('toplight')
    if is_microscope != '':
        create_lights(box2)

    label_text=text_status()
    status_label = GtkLabel(label_text)
    box2.pack_start(status_label)
    status_label.set_alignment(1, 0.5)
    status_label.show()

    thread.start_new_thread(update_status, (status_label,))

def update_status(label):
    while 1:
        text=text_status()
        threads_enter()
        update_all()
        label.set_text(text)
        threads_leave()
        try:
            time.sleep(1)
        except IOError:
            mainquit()

def update_all():
    changed_keys=camera.get_changed_keys()
    for key in changed_keys:
        value=camera.get_value(key)
        if cpia_debug:
            print key+' / '+value
        execute_callback(key)
    return

def text_status():
    text=camera.get_value('actual_fps')+' fps'+' / '+\
          camera.get_value('transfer_rate')
    return text

######################################################################
#
# main window
#
######################################################################

def create_main_window():
    
    # main window
    win = GtkWindow()
    win.set_name("CPiA control main")
    win.connect("destroy", do_exit)
    win.connect("delete_event", mainquit)
    win.set_title("CPiA control")

    mainbox = GtkVBox()
    win.add(mainbox)
    mainbox.show()

    menubar = GtkMenuBar()
    mainbox.pack_start(menubar, expand=FALSE)
    menubar.show()

    menuitem = GtkMenuItem("File")
    menuitem.set_submenu(create_file_menu())
    menubar.append(menuitem)
    menuitem.show()

    menuitem = GtkMenuItem("Help")
    menuitem.set_submenu(create_help_menu())
    menuitem.right_justify()
    menubar.append(menuitem)
    menuitem.show()

    notebook = GtkNotebook()
    notebook.set_tab_pos(POS_TOP)
    mainbox.pack_start(notebook)
    notebook.show()

    # create brightness/color/contrast
    create_picture(notebook)

    # create compression
    create_compression(notebook)

    # exposure
    create_exposure(notebook)
    
    # filter
    create_filter(notebook)
    
    # color balance
    create_color_balance(notebook)

    # create misc
    create_misc(notebook)


    # camera status
    if have_gtk!=0:
        create_status(mainbox)
    
    # show the stuff
    win.show()

def do_exit(button):
        mainquit()

def main(cam):
    global camera
    camera=cam
    try:
        create_main_window()
    except ValueError, val:
        print \
"""Ooops: probably you got a floating exception. If the error below
       is about a 'float() literal too large' you have encountered a
       python-gtk bug. Either upgrade to version 0.6.3 or greater or
       unset the locale settings (environment variables LANG and LC_*)
       and restart the application. In any other case please send me
       a bug report.
"""
        print val
        sys.exit(1)
    mainloop()
