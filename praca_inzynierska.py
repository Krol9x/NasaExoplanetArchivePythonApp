# -*- coding: utf-8 -*-
"""
Praca inżynierska "Aplikacja Desktopowa Nasa Exoplanet Archive"
@author: Hubert Król

"""

from io import StringIO
import requests
import pandas
import tkinter as tk
from tkinter import ttk
from tkinter import ttk, Tk, Entry, Button, Text, Label, END, Scale, Scrollbar
from tkinter import Canvas
import math
import pandas as pd
from tkinter import Tk, Label, Entry, Button, Scale, Scrollbar, ttk, StringVar, OptionMenu, Checkbutton, IntVar           
from tkinter import *
from tkinter import ttk     
from tkinter import Canvas

pi = 3.14159
au=1.496e11
rsun = 6.955e8 
G = 0.00029591220828559104 

sa = lambda m,P : (G*m*P**2/(4*pi**2) )**(1./3) 

def tap_query(base_url, query, dataframe=True):
    uri_full = base_url
    for k in query:
        if k != "format":
            uri_full += "{} {} ".format(k, query[k])
    
    uri_full = uri_full[:-1] + "&format={}".format(query.get("format","csv"))
    uri_full = uri_full.replace(' ','+')

    response = requests.get(uri_full, timeout=90)
    
    if dataframe:
        return preprocess_data(pd.read_csv(StringIO(response.text)))
    else:
        return response.text

def preprocess_data(data):
    
    grouped_data = data.groupby(['pl_name', 'hostname'])

 
    def process_group(group):
       
        default_1_rows = group[group['default_flag'] == 1]
        
        default_0_rows = group[group['default_flag'] == 0]

  
        base_row = default_1_rows.head(1)


        if not default_0_rows.empty:
          
            for col in base_row.columns:
                
                if pd.isna(base_row[col].iloc[0]):
                    non_nan_values = default_0_rows[col].dropna()
                    if not non_nan_values.empty:
                        base_row[col].iloc[0] = non_nan_values.iloc[0]
                        

        return base_row

   
    preprocessed_data = grouped_data.apply(process_group).reset_index(drop=True)

    return preprocessed_data
def fill_remaining_nans(data):
    
    columns_to_fill = ['pl_orbeccen', 'pl_ratdor', 'pl_orbincl']
    for col in columns_to_fill:
        data[col].fillna(0, inplace=True)
        
def new_scrape():
    uri_ipac_base = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query="
    uri_ipac_query = {
        "select": "pl_name,hostname,default_flag,pl_massj,pl_radj,pl_ratdor,sy_pnum,"
                  "pl_orbper,pl_orbeccen,cb_flag,st_lum,"
                  "pl_orbincl,pl_orblper,"
                  "st_teff,st_met,st_mass,st_rad,pl_orbsmax",
        "from": "ps",
        "where": "default_flag = 1 or default_flag = 0",
        "order by": "pl_name",
        "format": "csv"
    }

    original_data = tap_query(uri_ipac_base, uri_ipac_query)
    fill_remaining_nans(original_data)
    return original_data

def identify_planet_star_types(dataframe):
   
    dataframe['Planet Type'] = ""
    dataframe['Possible Types'] = ""
    dataframe['Planet Color'] = ""
    dataframe['Star Type'] = ""
    dataframe['Star Color'] = ""

    star_temperature_ranges = {
        (30000, 50000): ('Blue', 'Blue'),  
        (10000, 30000): ('Blue-White', 'LightBlue1'),  
        (7500, 10000): ('White', 'White'),
        (6000, 7500): ('Yellow-White', 'LightYellow1'), 
        (5200, 6000): ('Yellow', 'Yellow'),
        (3700, 5200): ('Orange', 'Orange'),
        (0, 3700): ('Red', 'Red')
    }

    planet_color_map = {
        'Super-Jupiter': 'Orange',
        'Mid-Jupiter': 'Yellow',
        'Sub-Jupiter': 'LightBlue1',
        'Midplanet': 'LightGray',
        'Super-Earth': 'LightGreen',
        'Mid-Earth': 'Green',
        'Sub-Earth': 'DarkGreen',
        'Unknown': 'Gray'
    }

    for index, row in dataframe.iterrows():
        star_temperature = row['st_teff']
        star_type = None
        star_color = None
        for temp_range, (type_name, color) in star_temperature_ranges.items():
            if temp_range[0] <= star_temperature <= temp_range[1]:
                star_type = type_name
                star_color = color
                break

        dataframe.at[index, 'Star Type'] = star_type
        if pd.isnull(star_color):
            dataframe.at[index, 'Star Color'] = 'Yellow'
        else:
            dataframe.at[index, 'Star Color'] = star_color

       
        planet_mass = float(row['pl_massj'])
        if 2 <= planet_mass:
            dataframe.at[index, 'Planet Type'] = 'Super-Jupiter'
            dataframe.at[index, 'Possible Types'] = 'gazowa'
        elif 0.5 <= planet_mass < 2:
            dataframe.at[index, 'Planet Type'] = 'Mid-Jupiter'
            dataframe.at[index, 'Possible Types'] = 'gazowa'
        elif 0.1 <= planet_mass < 0.5:
            dataframe.at[index, 'Planet Type'] = 'Sub-Jupiter'
            dataframe.at[index, 'Possible Types'] = 'gazowa lub pokryta lodem'
        elif 0.03 <= planet_mass < 0.1:
            dataframe.at[index, 'Planet Type'] = 'Midplanet'
            dataframe.at[index, 'Possible Types'] = 'skalista, pokryta Lodem lub gazowa'
        elif 0.003<= planet_mass < 0.03:
            dataframe.at[index, 'Planet Type'] = 'Super-Earth'
            dataframe.at[index, 'Possible Types'] = 'skalista, wodnista, pokryta lodem lub gazowa'
        elif 0.0015 <= planet_mass < 0.003:
            dataframe.at[index, 'Planet Type'] = 'Mid-Earth'
            dataframe.at[index, 'Possible Types'] = 'skalista, wodnista lub pokryta lodem'
        elif planet_mass < 0.0015:
            dataframe.at[index, 'Planet Type'] = 'Sub-Earth'
            dataframe.at[index, 'Possible Types'] = 'skalista'
        else:  
            dataframe.at[index, 'Planet Type'] = 'Unknown'
            dataframe.at[index, 'Possible Types'] = 'brak danych'

        planet_type = dataframe.at[index, 'Planet Type']
        if planet_type:
            dataframe.at[index, 'Planet Color'] = planet_color_map[planet_type]
        else:
            dataframe.at[index, 'Planet Color'] = 'Gray'

    return dataframe

def identify_cb_star(dataframe):
    dataframe['cb_flag'] = dataframe['cb_flag'].replace({1: 'Tak', 0: 'Nie'})
    return dataframe



from tkinter.ttk import Style
class PlanetDetailsWindow:
    def __init__(self, root, data):
        self.root = root
        self.root.title("Szczegóły")
        self.root.configure(bg='black')
        root.title("Szczegóły")
        root.configure(bg='black')
        
     
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        
        root.geometry(f"{screen_width - 20}x{screen_height - 80}+0+0")
        self.root.minsize(800, 800)
        self.data = data 
        self.selected_star = None  
        self.zoom_factor = 0.000001 
        #self.display_label = Label(self.root, bg='black', fg='white')
        #self.display_label.pack()
        self.details_frame = ttk.Frame(self.root)
        self.details_frame.pack(side=tk.TOP, anchor=tk.N)
        self.details_text = Text(self.details_frame, wrap=tk.WORD, width=100, height=8, bg='black', fg='white')
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.details_frame, orient='vertical', command=self.details_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.details_text.config(yscrollcommand=self.scrollbar.set)
        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(side=tk.TOP)
        self.display_label = Label(self.root, bg='black', fg='white')
        
        self.display_label.pack()
        self.left_right_visualization = ttk.Frame(self.root)
        
        toggle_frame = ttk.Frame(self.root)
        toggle_frame.pack(side=tk.TOP)
        
        self.show_canvas_button = Button(toggle_frame, text="Pokaż charakterystykę z orbitami", command=self.show_canvas, bg='white', fg='black')
        self.show_canvas_button.pack(side='left', padx=5, pady=5)

        self.show_comparison_button = Button(toggle_frame, text="Pokaż porównanie wielkości gwiazd i planet", command=self.show_comparison, bg='white', fg='black')
        self.show_comparison_button.pack(side='left', padx=5, pady=5)
        self.left_right = tk.Frame(self.root)
        self.left_right.pack(side='top')
        
       
        

      
        
        
        #self.display_label = Label(self.root, bg='black', fg='white')
        #self.display_label.pack()
        #self.display_label = Label(self.root, bg='black', fg='white')
        #self.display_label.pack()
    
        self.canvas = Canvas(self.root, width=800, height=400, bg='black')
        self.canvas.pack(side=tk.TOP)
 
        self.zoom_frame = ttk.Frame(self.root)
        self.zoom_frame.pack(side=tk.TOP)
        self.zoom_slider = ttk.Scale(self.zoom_frame, from_=0.0000001, to=1, orient=tk.HORIZONTAL, command=self.zoom, length=800)
        self.zoom_slider.set(self.zoom_factor)  
        self.zoom_slider.pack(side=tk.TOP, anchor=tk.SE, pady=1)
        self.zoom_label = Label(self.zoom_frame, text="Wartość zoomu: " + str(self.zoom_factor), bg='black', fg='white')
        self.zoom_label.pack(side=TOP, padx=5, pady=5)
        
        
        self.zoom_factor_entry = Entry(self.zoom_frame)
        self.zoom_factor_entry.pack(side=tk.TOP, padx=10, pady=10)
       
        self.apply_zoom_button = Button(self.zoom_frame, text="Zastosuj", command=self.apply_zoom, bg='white', fg='black')
        self.apply_zoom_button.pack(side=tk.TOP, padx=10, pady=10)
        
        
        
        self.left_right_visualization.pack(side='top')

        
        
        left_arrow_visualization = Button(self.left_right_visualization, text="lewo", command=lambda: self.scroll_visualization_canvas("lewo"), bg='white', fg='black')
        left_arrow_visualization.pack(side='left', padx=1, pady=1)
        
        right_arrow_visualization = Button(self.left_right_visualization, text="prawo", command=lambda: self.scroll_visualization_canvas("prawo"), bg='white', fg='black')
        right_arrow_visualization.pack(side='left', padx=1, pady=1)
        
        top_arrow_visualization = Button(self.left_right_visualization, text="góra", command=lambda: self.scroll_visualization_canvas("góra"), bg='white', fg='black')
        top_arrow_visualization.pack(side='left', padx=1, pady=1)
        
        down_arrow_visualization = Button(self.left_right_visualization, text="dół", command=lambda: self.scroll_visualization_canvas("dół"), bg='white', fg='black')
        down_arrow_visualization.pack(side='left', padx=1, pady=1)
        
        self.min_distance_val = None
        self.max_distance_val = None
        self.min_mass_val = None
        self.max_mass_val = None
        self.min_st_mass_val = None
        self.max_st_mass_val = None
        self.min_pnum_val = None
        self.max_pnum_val = None
        self.show_canvas()
        
    def zoom(self, scale_value):
        
        self.zoom_factor = float(scale_value)
        try:
            self.zoom_label.config(text="skala 1 : 1 000000000, zoom: " + str(1/(self.zoom_factor))) 
        except:
            pass
        if self.selected_star is not None:
            self.draw_star_and_planets(self.selected_star)
    def apply_zoom(self):
       
        
        try:
            new_zoom_factor = float(self.zoom_factor_entry.get())
            self.zoom_slider.set(new_zoom_factor * self.zoom_factor)
            self.zoom(str(new_zoom_factor * self.zoom_factor))
        except:
            pass

    
    def draw_star(self, star_radius, color, scaling_factor=10000):
       
        sun_radius_scale = 696340
        scaled_star_radius = (star_radius * sun_radius_scale * self.zoom_factor) / scaling_factor

        self.canvas.create_oval(
            400 - scaled_star_radius, 200 - scaled_star_radius,
            400 + scaled_star_radius, 200 + scaled_star_radius,
            fill=color, outline=color
        )
    def show_canvas(self):
        # Funkcja wyświetlająca canvas i ukrywająca inne elementy
        
        #self.display_label.pack()
        self.canvas.pack(side=tk.TOP)
        self.zoom_slider.pack(side=tk.TOP)
        self.zoom_frame.pack(side=tk.TOP)
        self.left_right_visualization.pack(side='top')
        self.hide_other_elements(["canvas_frame","left_right"])
        self.show_canvas_button['bg'] = 'grey' 
        self.show_comparison_button['bg'] = 'white' 
        
    def show_comparison(self):
        
        self.canvas_frame.pack_forget()
        self.canvas_frame.pack(side=tk.TOP)
        self.left_right.pack(side='top')
        self.hide_other_elements(["canvas", "zoom_slider","zoom_frame","left_right_visualization"])
        self.show_canvas_button['bg'] = 'white' 
        self.show_comparison_button['bg'] = 'grey' 
     
    
    def hide_other_elements(self, elements_to_hide):
        
        for element in elements_to_hide:
            getattr(self, element).pack_forget() 
            
            
    def draw_star2(self, star_radius, st_mass, color, scaling_factor=10000):
        
        sun_radius_scale = 696340
        scaled_star_radius = (star_radius * sun_radius_scale * self.zoom_factor) / scaling_factor
    
        original_distance_between_stars = (st_mass / 2) * 10000
    
        distance_between_stars = original_distance_between_stars * self.zoom_factor
    
        center_x = 400
        center_y = 200
        midpoint_x = center_x - distance_between_stars / 2
        midpoint_y = center_y
    
        orbit_radius = distance_between_stars / 2
        self.canvas.create_oval(
            center_x - orbit_radius, center_y - orbit_radius,
            center_x + orbit_radius, center_y + orbit_radius,
            outline=color, dash=(3, 3)
        )
    
        self.canvas.create_oval(
            midpoint_x - scaled_star_radius, center_y - scaled_star_radius,
            midpoint_x + scaled_star_radius, center_y + scaled_star_radius,
            fill=color, outline=color
        )
        self.canvas.create_text(
            midpoint_x, center_y + scaled_star_radius + 10,
            text=f"{self.selected_star}a", fill='white'
        )
    
        self.canvas.create_oval(
            midpoint_x + distance_between_stars - scaled_star_radius, center_y - scaled_star_radius,
            midpoint_x + distance_between_stars + scaled_star_radius, center_y + scaled_star_radius,
            fill=color, outline=color
        )
        self.canvas.create_text(
            midpoint_x + distance_between_stars, center_y + scaled_star_radius + 10,
            text=f"{self.selected_star}b", fill='white'
        )
    def scroll_visualization_canvas(self, direction):
        delta_factor = 0.1
    
        if direction == "lewo":
            self.canvas.xview_scroll(int(-1 * delta_factor * 10), "units")
        elif direction == "prawo":
            self.canvas.xview_scroll(int(delta_factor * 10), "units")
        elif direction == "góra":
            self.canvas.yview_scroll(int(-1 * delta_factor * 10), "units")
        elif direction == "dół":
            self.canvas.yview_scroll(int(delta_factor * 10), "units")
            
    def draw_orbits_and_planets_2(self, selected_star_data, distance_between_stars):
        num_planets = selected_star_data.shape[0]
        angle_increment = 2 * math.pi / num_planets
        star_x_a, star_y_a = 400 - distance_between_stars / 2, 200 
        star_x_b, star_y_b = 400 + distance_between_stars / 2, 200  
    
        center_x = (star_x_a + star_x_b) / 2
        center_y = (star_y_a + star_y_b) / 2
    
        for i in range(num_planets):
            pl_orbsmax = selected_star_data['pl_orbsmax'].iloc[i] + (distance_between_stars / 2)
            pl_orbeccen = selected_star_data['pl_orbeccen'].iloc[i]
    
            semi_major_axis = ( (pl_orbsmax * (1 + pl_orbeccen)) / 2 * (149597871 * self.zoom_factor) ) /10000
    
            semi_minor_axis = semi_major_axis * math.sqrt(1 - pl_orbeccen ** 2)
    
            angle = i * angle_increment
    
            x_position = center_x + semi_major_axis * math.cos(angle)
            y_position = center_y + semi_minor_axis * math.sin(angle)
    
            self.canvas.create_oval(center_x - semi_major_axis, center_y - semi_minor_axis,
                                    center_x + semi_major_axis, center_y + semi_minor_axis,
                                    outline='white')
    
            self.canvas.create_line(center_x, center_y, x_position, y_position, fill='white')
    
            planet_name = selected_star_data['pl_name'].iloc[i]
            planet_radius = selected_star_data['pl_radj'].iloc[i] * 10 * self.zoom_factor
            self.canvas.create_oval(x_position - planet_radius, y_position - planet_radius,
                                    x_position + planet_radius, y_position + planet_radius,
                                    outline=selected_star_data['Planet Color'].iloc[i], fill=selected_star_data['Planet Color'].iloc[i])
    
            self.canvas.create_text(x_position, y_position + planet_radius + 10, text=planet_name, fill='white')

    def draw_orbits_and_planets(self, selected_star_data):

        num_planets = selected_star_data.shape[0]
        angle_increment = 2 * math.pi / num_planets
    
        star_x, star_y = 400, 200
    
        for i in range(num_planets):
            pl_orbsmax = selected_star_data['pl_orbsmax'].iloc[i]
            pl_orbeccen = selected_star_data['pl_orbeccen'].iloc[i]
    
            semi_major_axis = (pl_orbsmax * (1 + pl_orbeccen)) / 2 * (149597871 / 10000) * self.zoom_factor
    
            semi_minor_axis = semi_major_axis * math.sqrt(1 - pl_orbeccen ** 2)
    
            angle = i * angle_increment
    
            x_position = star_x + semi_major_axis * math.cos(angle)
            y_position = star_y + semi_minor_axis * math.sin(angle)
    
            self.canvas.create_oval(star_x - semi_major_axis, star_y - semi_minor_axis, star_x + semi_major_axis,
                                    star_y + semi_minor_axis, outline='white')
    
            self.canvas.create_line(star_x, star_y, x_position, y_position, fill=selected_star_data['Planet Color'].iloc[i])
    
            planet_name = selected_star_data['pl_name'].iloc[i]
            planet_radius = selected_star_data['pl_radj'].iloc[i] * 10 * self.zoom_factor
            self.canvas.create_oval(x_position - planet_radius, y_position - planet_radius,
                                     x_position + planet_radius, y_position + planet_radius,
                                     outline=selected_star_data['Planet Color'].iloc[i], fill=selected_star_data['Planet Color'].iloc[i])
    
            self.canvas.create_text(x_position, y_position + planet_radius + 10, text=planet_name, fill='white')
        
    def draw_star_and_planets(self, selected_star):

        self.canvas.delete("all")
        
        cb_flag = 'Nie'

        self.selected_star = selected_star
    
        selected_star_data = self.data[self.data['hostname'] == selected_star]
        
        selected_star_data = selected_star_data.dropna(subset=['pl_orbsmax'])

        selected_star_data.loc[selected_star_data['pl_radj'].isna() & selected_star_data['pl_orbsmax'].notna(), 'pl_radj'] = 1.0

        if selected_star_data['pl_orbsmax'].notna().any() and selected_star_data['st_rad'].isna().any():
            selected_star_data['st_rad'].fillna(1.0, inplace=True)
            selected_star_data['st_mass'].fillna(1.0, inplace=True)
        
        self.display_label = Label(self.root, bg='black', fg='white')

        try:
            cb_flag = selected_star_data['cb_flag'].iloc[0]
        except:
            pass
        if cb_flag == 'Tak':
            try:
                self.draw_star2(selected_star_data['st_rad'].iloc[0], selected_star_data['st_mass'].iloc[0], selected_star_data['Star Color'].iloc[0])
    
                distance_between_stars = (selected_star_data['st_mass'].iloc[0] / 2) 
    
                self.draw_orbits_and_planets_2(selected_star_data, distance_between_stars)
            except:
                pass
        else:
            try:
                self.draw_star(selected_star_data['st_rad'].iloc[0], selected_star_data['Star Color'].iloc[0])
                self.draw_orbits_and_planets(selected_star_data)
            
            except:
                pass
       
        
    def show_details(self, selected_star):
       
        self.details_text.delete('1.0', END)

        selected_star_data = self.data[self.data['hostname'] == selected_star]
        
        self.details_text.insert(END, "Nazwa Systemu: {}\n".format(selected_star))
        
        self.details_text.insert(END, "Wszystkie Gwiazdy:\n")
        related_star_names = selected_star_data['hostname'].unique()
        
        cb_flag = selected_star_data['cb_flag'].iloc[0]
        related_star_names = selected_star_data['hostname'].tolist()
        related_star_info = selected_star_data['Star Type'].tolist()
        related_star_info1 = selected_star_data['st_mass'].tolist()
        related_star_info2 = selected_star_data['st_rad'].tolist()
        related_star_info3 = selected_star_data['st_lum'].tolist()
        if cb_flag == 'Tak':
            for star_name, star_info, star_info1, star_info2, star_info3 in zip(related_star_names, related_star_info, related_star_info1, related_star_info2, related_star_info3):
                self.details_text.insert(END, "- {} a Typ Gwiazdy: {}, Masa Gwiazdy: {},  Promień Gwiazdy: {} Ilość emitowanej energii: {}\n".format(star_name, star_info, star_info1, star_info2, star_info3))
                self.details_text.insert(END, "- {} b Typ Gwiazdy: {}, Masa Gwiazdy: {},  Promień Gwiazdy: {} Ilość emitowanej energii: {}\n".format(star_name, star_info, star_info1, star_info2, star_info3))
                break
        else:
            for star_name, star_info, star_info1, star_info2, star_info3 in zip(related_star_names, related_star_info, related_star_info1, related_star_info2, related_star_info3):
                self.details_text.insert(END, "- {} a Typ Gwiazdy: {}, Masa Gwiazdy: {},  Promień Gwiazdy: {} Ilość emitowanej energii: {}\n".format(star_name, star_info, star_info1, star_info2, star_info3))
                break

        self.details_text.insert(END, "\nPlanety w systemie:\n")
        related_planet_names = selected_star_data['pl_name'].tolist()
        related_planet_info = selected_star_data['pl_radj'].tolist()
        related_planet_info1 = selected_star_data['pl_orbsmax'].tolist()
        related_planet_info2 = selected_star_data['pl_massj'].tolist()
        related_planet_info3 = selected_star_data['pl_orbeccen'].tolist()
        related_planet_info4 = selected_star_data['Planet Type'].tolist()
        related_planet_info5 = selected_star_data['Possible Types'].tolist()
        related_planet_info6 = selected_star_data['pl_orblper'].tolist()
        for planet_name, planet_info, planet_info1, planet_info2, planet_info3, planet_info4, planet_info5, planet_info6 in zip(related_planet_names, related_planet_info, related_planet_info1, related_planet_info2, related_planet_info3, related_planet_info4, related_planet_info5, related_planet_info6):
           self.details_text.insert(END, "- {} (Promień: {}, dystans od gwiazdy: {}, masa: {}, elipsa orbity: {}, typ planety: {}, możliwe warunki: {}, Ile dni zajmuje pełny obieg: {})\n".format(planet_name, planet_info, planet_info1, planet_info2, planet_info3, planet_info4, planet_info5, planet_info6))
        self.details_text.pack(side=tk.LEFT, anchor=tk.SE)


    def draw_comparison(self, system_data, scaling_factor=10000, planet_gap=100):

        cb_flag = 0

        canvas = Canvas(self.canvas_frame, width=800, height=400, bg='black')
        canvas.pack(side=tk.BOTTOM, anchor=tk.SE, expand=True, fill=tk.BOTH)
    
        sun_radius_scale = 696340/5
        planet_radius_scale = 69911/5
        x_position = 50 
        y_position = 200 
  
        previous_object_radius = 0
        system_data_star = system_data.copy()
        system_data_star = system_data_star.drop_duplicates(subset=['hostname'], keep='first')
       
        try:
            cb_flag = system_data_star['cb_flag'].iloc[0]
        except:
            pass
        
        if cb_flag == 'Tak':
            system_data_star.loc[len(system_data_star)] = system_data_star.iloc[0]
            system_data_star = system_data_star.reset_index(drop=True)
            system_data_star.at[0,'hostname'] = str(system_data_star.at[0,'hostname']) + ' a'
            system_data_star.at[1,'hostname'] = str(system_data_star.at[1,'hostname']) + ' b'
        else:
            pass
        
        system_data_star = system_data_star.dropna(subset=['st_rad'])
        for index, star_data in system_data_star.iterrows():

            star_radius = (star_data['st_rad'] * sun_radius_scale) / scaling_factor
            
            x_position += previous_object_radius + star_radius + 150
            
            canvas.create_oval(
                x_position, y_position - star_radius,
                x_position + 2 * star_radius, y_position + star_radius,
                fill=star_data['Star Color'], outline=star_data['Star Color']
            )
            
            canvas.create_text(
                x_position + star_radius, y_position - star_radius - 10,
                text=star_data['hostname'], fill='white'
            )
            
            previous_object_radius = max(star_radius * 2, 0)
                    

        system_data = system_data.dropna(subset=['pl_radj'])
        
        for index, planet_data in system_data.iterrows():
                planet_radius = (planet_data['pl_radj'] * planet_radius_scale) / scaling_factor
            
                object_width = 2 * max(previous_object_radius, planet_radius)
            
                x_position += object_width + planet_gap
            
                canvas.create_oval(
                    x_position, y_position - planet_radius,
                    x_position + 2 * planet_radius, y_position + planet_radius,
                    fill=planet_data['Planet Color'], outline=planet_data['Planet Color']
                )
            
                canvas.create_text(
                    x_position + planet_radius, y_position - planet_radius - 10,
                    text=planet_data['pl_name'], fill='white'
                )
            
                x_position += 2 * planet_radius
                previous_object_radius = planet_radius
            
        self.root.update()
            


        left_arrow = Button(self.left_right, text="<", command=lambda: self.scroll_canvas(canvas, "left"), bg='white', fg='black')
        left_arrow.pack(side='left')

        right_arrow = Button(self.left_right, text=">", command=lambda: self.scroll_canvas(canvas, "right"), bg='white', fg='black')
        right_arrow.pack(side='left')

    def scroll_canvas(self, canvas, direction):
        delta_factor = 0.1

        if direction == "left":
            canvas.xview_scroll(int(-1 * delta_factor * 10), "units")
        elif direction == "right":
            canvas.xview_scroll(int(delta_factor * 10), "units")



class PlanetSearchApp(tk.Frame):
    def __init__(self, root, data, md2):
        super().__init__(root)
        self.root = root
        self.root.title("Aplikacja Nasa Exoplanet Archive")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        root.geometry(f"{screen_width - 20}x{screen_height - 80}+0+0")
        self.root.minsize(600, 950)
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.config(bg="blue")  
    
        self.data = data
        self.min_distance = min(self.data['pl_orbsmax'])
        self.max_distance = max(self.data['pl_orbsmax'])
        
        self.min_st_mass_value = min(self.data['st_mass'])
        self.max_st_mass_value = max(self.data['st_mass'])
        for i in range(len(self.data)):
            if math.isnan(self.data.at[i,'pl_massj']):
                self.data.at[i,'pl_massj'] = 0
        self.min_mass_value = min(self.data['pl_massj'])
        self.max_mass_value = max(self.data['pl_massj'])  
        
        self.min_pnum_value = 1
        self.max_pnum_value = max(self.data['sy_pnum'])  
        self.show_pnum_var = tk.IntVar()
        #self.root.update_idletasks() 
        #self.result_frame_width = self.root.winfo_width()-20
        self.root.bind("<Configure>", self.on_configure)
        self.create_canvas()
        self.start_search()
    def on_configure(self, event):
        self.update_result_frame_width(event)
        self.update_filter_layout(event)
    def create_canvas(self):
        self.canvas = tk.Canvas(self.main_frame, bg="black")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.inner_frame = tk.Frame(self.canvas, bg="black")
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw", tags="inner_frame")
        self.inner_frame.bind("<Configure>", self.onInnerFrameConfigure)
        self.canvas.bind("<Configure>", self.onCanvasConfigure)
        
        self.create_widgets()
        
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    def onCanvasConfigure(self, event):
        self.canvas.itemconfigure("inner_frame", width=self.result_frame_width)
    
    def onInnerFrameConfigure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_treeview_configure(self, tree):
        tree.update_idletasks()
        width = sum(tree.column(col, width=None) for col in tree['columns'])
        self.result_frame_width = width
        self.result_frame.configure(width=width)
    def update_result_frame_width(self, event):
        
        self.result_frame_width = self.root.winfo_width()-20
    def create_widgets(self):
        
        window_width = self.root.winfo_width()
        column_names_mapping = {
        'pl_orbsmax': 'Odległość orbity (AU)',
        'st_mass': 'Masa gwiazdy (M☉)',
        'pl_massj': 'Masa planety (MJ)',
        'pl_name': 'Nazwa planety',
        'cb_flag': 'Gwiazda binarna',
        'pl_radj': 'Promień planety (RJ)',
        'pl_orbper': 'Czas okrązenia (Dni)',
        'st_met': 'Zawartość metanu (dex)',
        'hostname': 'Nazwa układu',
        'sy_pnum': 'Liczba planet',
        'st_rad': 'Promień gwiazdy (R☉)',
        'pl_orbeccen': 'Eliptyczność orbit',
        'Star Color': 'Kolor gwiazdy',
        'Star Type': 'Typ gwiazdy',
        'Planet Type': 'Typ planety',
        'Planet Color': 'Kolor planety',
        'Possible Types': 'Możliwe typy planet',
        'st_teff': 'Temperatura gwiazdy[K]',
        'st_lum': 'Emitowana energia',
        'pl_orbiper': 'Kątowy Dystans',
        'default_flag': 'Domyślny wiersz',
        'pl_ratdor': 'Odległość w połowie tranzytu',
        }
        self.result_frame = tk.Frame(self.inner_frame)
        self.result_frame.pack(fill="both", expand=True)
        
        self.result_tree = ttk.Treeview(self.result_frame, columns=list(self.data.columns), show="headings", style="Treeview", padding=0, height=40)
    
        for col in self.data.columns:
            column_name = column_names_mapping.get(col, col)
            self.result_tree.heading(col, text=column_name)
            self.result_tree.column(col, stretch=True)
        
        self.tree_scrollbar_y = tk.Scrollbar(self.result_frame, orient="vertical", command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=self.tree_scrollbar_y.set)
        self.tree_scrollbar_y.pack(side="right", fill="y")
        
        self.tree_scrollbar_x = tk.Scrollbar(self.result_frame, orient="horizontal", command=self.result_tree.xview)
        self.result_tree.configure(xscrollcommand=self.tree_scrollbar_x.set)
        self.tree_scrollbar_x.pack(side="bottom", fill="x")
        
        self.result_tree.pack(fill="both", expand=True)
        self.result_tree.bind("<Configure>", lambda event, tree=self.result_tree: self.on_treeview_configure(tree))
        self.result_tree.bind("<ButtonRelease-1>", self.show_selected_details)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="black", foreground="white")
        style.configure("Treeview.Heading", background="white")
        
        self.search_button = tk.Button(self.inner_frame, text="Szukaj", command=self.search_planet, bg='white', fg='black', relief=tk.FLAT, borderwidth=0, cursor='hand2')
        self.search_button.pack(pady=10, padx=10, side=tk.TOP, ipadx=10, ipady=10)
        self.search_button.bind("<Enter>", lambda event: self.search_button.config(bg="grey"))
        self.search_button.bind("<Leave>", lambda event: self.search_button.config(bg="white"))
        self.filter_frame = tk.Frame(self.inner_frame, bg='black')
        self.filter_frame.pack(pady=10, padx=10, fill='x')
        
        self.show_distance_var = tk.IntVar()
        self.show_mass_var = tk.IntVar()
        self.show_star_type_var = tk.IntVar()
        self.show_planet_type_var = tk.IntVar()
        self.show_cb_filter_var = tk.IntVar()
        self.show_st_mass_var = tk.IntVar()
        self.show_distance_var = IntVar()
        self.show_mass_var = IntVar()
        self.show_star_type_var = IntVar()
        self.show_planet_type_var = IntVar()
        self.show_cb_filter_var = IntVar()
        self.show_st_mass_var = IntVar()

        self.distance_checkbox = Checkbutton(self.filter_frame, text="Pokaż filtr Dystansu", variable=self.show_distance_var,
                                             command=self.toggle_distance_filter, bg='black', fg='white', selectcolor='black')
        self.st_mass_checkbox = Checkbutton(self.filter_frame, text="Pokaż filtr masy gwiazdy", variable=self.show_st_mass_var,
                                             command=self.toggle_st_mass_filter, bg='black', fg='white', selectcolor='black')
        self.mass_checkbox = Checkbutton(self.filter_frame, text="Pokaż filtr masy planety", variable=self.show_mass_var,
                                         command=self.toggle_mass_filter, bg='black', fg='white', selectcolor='black')
        self.star_type_checkbox = Checkbutton(self.filter_frame, text="Pokaż filtr typu gwiazdy", variable=self.show_star_type_var,
                                              command=self.toggle_star_type_filter, bg='black', fg='white', selectcolor='black')
        self.planet_type_checkbox = Checkbutton(self.filter_frame, text="Pokaż filtr typu planety", variable=self.show_planet_type_var,
                                                command=self.toggle_planet_type_filter, bg='black', fg='white', selectcolor='black')
        self.cb_filter_checkbox = Checkbutton(self.filter_frame, text="Pokaż Filtr gwiazdy binarnej", variable=self.show_cb_filter_var,
                                              command=self.toggle_cb_filter, bg='black', fg='white', selectcolor='black')
        self.pnum_checkbox = Checkbutton(self.filter_frame, text="Pokaż filtr ilości planet", variable=self.show_pnum_var,
                                   command=self.toggle_pnum_filter, bg='black', fg='white', selectcolor='black')  


        self.checkboxes = [self.distance_checkbox, self.mass_checkbox, self.star_type_checkbox, self.planet_type_checkbox,
                           self.cb_filter_checkbox, self.st_mass_checkbox, self.pnum_checkbox] 

        for checkbox in self.checkboxes:
            checkbox.pack(side=LEFT, padx=10)

        self.cb_flag_label = Label(self.inner_frame, text="Circumbinary Filter", bg='black', fg='white')
        self.value_label_map = {
            "0": "No",
            "1": "Yes"
        }
        self.cb_option_var = StringVar(self.inner_frame)
        self.cb_option_var.set("") 
        self.cb_option_dropdown = OptionMenu(self.inner_frame, self.cb_option_var, "", "Tak", "Nie")
        self.cb_option_dropdown.config(bg='black', fg='white')

        self.search_label = Label(self.inner_frame, text="Wpisz nazwę planety lub układu:", bg='black', fg='white')
        self.search_label.pack(pady=10, padx=10, side=LEFT)
        self.search_entry = Entry(self.inner_frame)
        self.search_entry.pack(pady=10, padx=10, side=LEFT)
        self.star_type_label = Label(self.inner_frame, text="Filtr typu gwiazdy", bg='black', fg='white')
        
        star_types = self.data['Star Type'].unique()
        self.selected_star_type = StringVar(self.inner_frame)
        self.selected_star_type.set(star_types[0])

        self.star_type_dropdown = OptionMenu(self.inner_frame, self.selected_star_type, *star_types)
        self.star_type_dropdown.config(bg='black', fg='white')
        self.planet_type_label = Label(self.inner_frame, text="Filtr typu planety", bg='black', fg='white')

        planet_types = self.data['Planet Type'].unique()
        self.selected_planet_type = StringVar(self.inner_frame)
        self.selected_planet_type.set(planet_types[0])

        self.planet_type_dropdown = OptionMenu(self.inner_frame, self.selected_planet_type, *planet_types)
        self.planet_type_dropdown.config(bg='black', fg='white')
        
        self.min_scale = Scale(self.inner_frame, from_=self.min_distance, to=self.max_distance, orient='horizontal', length=150,
                                  label="Minimalny dystans od gwiazdy", bg='black', fg='white', resolution=0.01, command=self.update_min_distance)
        self.min_scale.pack()
       
        self.max_scale = Scale(self.inner_frame, from_=self.min_distance, to=self.max_distance, orient='horizontal', length=150,
                                  label="Maksymalny dystans od gwiazdy", bg='black', fg='white', resolution=0.01, command=self.update_max_distance)
        self.max_scale.pack()

        self.min_mass = Scale(self.inner_frame, from_=float(self.min_mass_value), to=float(self.max_mass_value), orient='horizontal', length=150, label="Minimalna masa planety",
                               bg='black', fg='white', resolution=0.01, command=self.update_max_mass)
        self.min_mass.pack()
        
        self.max_mass = Scale(self.inner_frame, from_=float(self.min_mass_value), to=float(self.max_mass_value), orient='horizontal', length=150, label="Maksymalna masa planety",
                               bg='black', fg='white', resolution=0.01, command=self.update_max_mass)
        self.max_mass.pack()
        
        self.min_st_mass = Scale(self.inner_frame, from_=self.min_st_mass_value, to=self.max_st_mass_value, orient='horizontal', length=150, label="Minimalna masa gwiazdy",
                                  bg='black', fg='white', resolution=0.01,  command=self.update_min_st_mass)
        self.min_st_mass.pack()
        
        self.max_st_mass = Scale(self.inner_frame, from_=self.min_st_mass_value, to=self.max_st_mass_value, orient='horizontal', length=150, label="Maksymalna masa gwiazdy",
                                  bg='black', fg='white', resolution=0.01,  command=self.update_max_st_mass)
        self.max_st_mass.pack()
        
        
        min_pnum = 0
        max_pnum = max(self.data['sy_pnum']) 
        self.pnum_label = Label(self.inner_frame, text="Filter ilosci planet", bg='black', fg='white')

       
        self.pnum_label1 = Label(self.inner_frame, text="Minimalna liczba planet:", bg='black', fg='white')
        self.min_pnum = Spinbox(self.inner_frame, from_=self.min_pnum_value, to=self.max_pnum_value, width=5, bg='black', fg='white', command=self.update_min_pnum)
        self.min_pnum.pack()
        self.pnum_label2 = Label(self.inner_frame, text="Maksymalna liczba planet:", bg='black', fg='white')
        self.max_pnum = Spinbox(self.inner_frame, from_=self.min_pnum_value, to=self.max_pnum_value, width=5, bg='black', fg='white', command=self.update_max_pnum)
        self.max_pnum.pack()
        
        if self.inner_frame.winfo_width() < 900:
            self.min_scale.pack(pady=10, padx=10, side=TOP)
            self.max_scale.pack(pady=10, padx=10, side=TOP)
            self.min_mass.pack(pady=10, padx=10, side=TOP)
            self.max_mass.pack(pady=10, padx=10, side=TOP)
            self.min_st_mass.pack(pady=10, padx=10, side=TOP)
            self.max_st_mass.pack(pady=10, padx=10, side=TOP)
            self.min_pnum.pack(pady=10, padx=10, side=TOP)
            self.max_pnum.pack(pady=10, padx=10, side=TOP)
        else:
            self.min_distance.pack(pady=10, padx=10, side=LEFT)
            self.max_distance.pack(pady=10, padx=10, side=LEFT)
            self.min_mass.pack(pady=10, padx=10, side=LEFT)
            self.max_mass.pack(pady=10, padx=10, side=LEFT)
            self.min_st_mass.pack(pady=10, padx=10, side=LEFT)
            self.max_st_mass.pack(pady=10, padx=10, side=LEFT)
            self.min_pnum.pack(pady=10, padx=10, side=LEFT)
            self.max_pnum.pack(pady=10, padx=10, side=LEFT)
        
        self.hide_filters()
        
    def update_min_distance(self, value):
        self.min_distance = float(value)
        self.max_scale.config(from_=self.min_distance)
    def update_max_distance(self, value):
        self.max_distance = float(value)
        self.min_scale.config(to=self.max_distance)  
    def update_min_st_mass(self, value):
        self.min_st_mass_value = float(value)
        self.max_st_mass.config(from_=self.min_st_mass_value)  
    def update_max_st_mass(self, value):
        self.max_st_mass_value = float(value)
        self.min_st_mass.config(to_=self.max_st_mass_value)  
    def update_max_pnum(self):
        self.max_pnum_value = int(self.max_pnum.get())
        self.min_pnum.config(to=self.max_pnum.get())   
    def update_min_pnum(self):
        self.min_pnum_value = int(self.min_pnum.get())
        self.max_pnum.config(from_=self.min_pnum_value)
    def update_min_mass(self, value):
        self.min_mass_value = float(value)
        self.max_mass.config(from_=self.min_mass_value)  
    def update_max_mass(self, value):
        self.max_mass_value = float(value)
        self.min_mass.config(to_=self.max_mass_value)  
    
    def search_planet2(self, filters=None):
        search_term = self.search_entry.get().strip()
        
        filtered_data = self.data.copy()
    
        self.display_result(filtered_data)
    
    def start_search(self):
    
        self.search_planet2()
 
    def mouse_wheel_scroll(self, event):
        
        if event.delta:
            self.main_frame.yview_scroll(-1*(event.delta/120), "units")
    def update_layout(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def limit_checkboxes(self, *args):

        num_checked = sum(var.get() for var in self.checkbox_vars)
    
        if num_checked > 2:
            for checkbox, var in zip(self.checkboxes, self.checkbox_vars):
                if not var.get():
                    checkbox.config(state="disabled")
        else:
            for checkbox in self.checkboxes:
                checkbox.config(state="normal")

    def toggle_distance_filter(self):
        if self.show_distance_var.get():


                self.max_scale.pack(pady=3, padx=3, side=TOP)
                self.min_scale.pack(pady=3, padx=3, side=TOP)
        else:
            self.max_scale.pack_forget()
            self.min_scale.pack_forget()

    def toggle_mass_filter(self):
        if self.show_mass_var.get():

                self.min_mass.pack(pady=3, padx=3, side=TOP)
                self.max_mass.pack(pady=3, padx=3, side=TOP)
        else:
            self.min_mass.pack_forget()
            self.max_mass.pack_forget()

    def toggle_star_type_filter(self):
        if self.show_star_type_var.get():
                self.star_type_label.pack(pady=3, padx=3, side=TOP)
                self.star_type_dropdown.pack(pady=3, padx=3, side=TOP)
        else:
            self.star_type_label.pack_forget()
            self.star_type_dropdown.pack_forget()

    def toggle_planet_type_filter(self):
        if self.show_planet_type_var.get():
                self.planet_type_label.pack(pady=3, padx=3, side=TOP)
                self.planet_type_dropdown.pack(pady=3, padx=3, side=TOP)
        else:
            self.planet_type_label.pack_forget()
            self.planet_type_dropdown.pack_forget()

    def toggle_cb_filter(self):
        if self.show_cb_filter_var.get():
               self.cb_flag_label.pack(side=TOP, padx=10, pady=5)
               self.cb_option_dropdown.pack(pady=3, padx=3, side=TOP)
  
        else:
            self.cb_option_dropdown.pack_forget()
            self.cb_flag_label.pack_forget()

    def toggle_st_mass_filter(self): 
        if self.show_st_mass_var.get():
                self.min_st_mass.pack(pady=3, padx=3, side=TOP)
                self.max_st_mass.pack(pady=3, padx=3, side=TOP)
        else:
            self.min_st_mass.pack_forget()
            self.max_st_mass.pack_forget()
    def toggle_pnum_filter(self):
        if self.show_pnum_var.get():
                    self.pnum_label.pack(side=TOP, padx=10, pady=5)
                    self.pnum_label1.pack(side=TOP, padx=10, pady=5)
                    self.min_pnum.pack(pady=3, padx=3, side=TOP)
                    self.pnum_label2.pack(side=TOP, padx=10, pady=5)
                    self.max_pnum.pack(pady=3, padx=3, side=TOP)
                    
        else:
            self.min_pnum.pack_forget()
            self.max_pnum.pack_forget()
            self.pnum_label.pack_forget()
            self.pnum_label1.pack_forget()
            self.pnum_label2.pack_forget()
            
    def hide_filters(self):
        self.toggle_distance_filter()
        self.toggle_mass_filter()
        self.toggle_star_type_filter()
        self.toggle_planet_type_filter()
        self.toggle_cb_filter()
        self.toggle_st_mass_filter()
        self.toggle_pnum_filter()  
        
    def search_planet(self):
        search_term = self.search_entry.get().strip()
        
        filtered_data = self.data.copy()
    
        if self.show_distance_var.get():
            min_distance = self.min_scale.get()
            max_distance = self.max_scale.get()
            filtered_data = filtered_data[
                (min_distance <= filtered_data['pl_orbsmax']) & (filtered_data['pl_orbsmax'] <= max_distance)
            ]
    
        if self.show_mass_var.get():
            min_mass = self.min_mass.get()
            max_mass = self.max_mass.get()
            filtered_data = filtered_data[
                (min_mass <= filtered_data['pl_massj']) & (filtered_data['pl_massj'] <= max_mass)
            ]
    
        if self.show_star_type_var.get():
            selected_star_type = self.selected_star_type.get()
            filtered_data = filtered_data[filtered_data['Star Type'] == selected_star_type]
    
        if self.show_planet_type_var.get():
            selected_planet_type = self.selected_planet_type.get()
            filtered_data = filtered_data[filtered_data['Planet Type'] == selected_planet_type]

        if self.show_cb_filter_var.get():
            cb_option = self.cb_option_var.get()
            if cb_option:
                filtered_data = filtered_data[filtered_data['cb_flag'] == cb_option]
                
        if self.show_st_mass_var.get():
            min_st_mass = self.min_st_mass.get()
            max_st_mass = self.max_st_mass.get()
            filtered_data = filtered_data[
                (min_st_mass <= filtered_data['st_mass']) & (filtered_data['st_mass'] <= max_st_mass)
            ]
            
        if self.show_pnum_var.get():
            min_pnum = int(self.min_pnum.get())
            max_pnum = int(self.max_pnum.get())
            filtered_data = filtered_data[
                (min_pnum <= filtered_data['sy_pnum']) & (filtered_data['sy_pnum'] <= max_pnum)
            ]
            
        if search_term:
            filtered_data = filtered_data[
                (filtered_data['pl_name'].str.contains(search_term, case=False)) |
                (filtered_data['hostname'].str.contains(search_term, case=False))
            ]
    
        self.display_result(filtered_data)

    def display_result(self, result):
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        if not result.empty:
            for index, row in result.iterrows():
                self.result_tree.insert("", "end", values=list(row))

    def show_selected_details(self, event):
        selected_item = self.result_tree.selection()
        if selected_item:
            selected_star = self.result_tree.item(selected_item, "values")[1]
            details_window = Tk()
            details_window.title("Planet Details")
            details_app = PlanetDetailsWindow(details_window, self.data)
            details_app.show_details(selected_star)
            details_app.draw_comparison(self.data[self.data['hostname'] == selected_star])
            details_app.draw_star_and_planets(selected_star)
            details_window.mainloop()
            
    def update_filters(self, event=None):
        if self.show_distance_var.get():
            self.toggle_distance_filter()
    
        if self.show_mass_var.get():
            self.toggle_mass_filter()
    
        if self.show_star_type_var.get():
            self.toggle_star_type_filter()
    
        if self.show_planet_type_var.get():
            self.toggle_planet_type_filter()
    
        if self.show_cb_filter_var.get():
            self.toggle_cb_filter()
    
        if self.show_st_mass_var.get():
            self.toggle_st_mass_filter()
    
        if self.show_pnum_var.get():
            self.toggle_pnum_filter()
            
    def update_filter_layout(self, event=None):
        
        window_width = self.root.winfo_width()

        if window_width < 1100:
            for checkbox in self.checkboxes:
                checkbox.pack_forget()
                checkbox.pack(side=TOP, anchor=W, padx=10, pady=5)
        else:
            for checkbox in self.checkboxes:
                checkbox.pack_forget()
                checkbox.pack(side=LEFT, padx=10)


if __name__ == "__main__":
    modified_data = new_scrape()
    modified_data_with_types = identify_planet_star_types(modified_data)
    modified_data_with_types = identify_cb_star(modified_data_with_types)
    md2 = modified_data_with_types[['pl_name', 'hostname', 'pl_radj', 'st_rad','pl_orbsmax', 'pl_orbeccen', 'cb_flag', 'st_mass','Star Color','Planet Color', 'pl_massj','Star Type','st_lum', 'pl_orbper']]
    app_root = Tk()
    planet_search_app = PlanetSearchApp(app_root, modified_data_with_types,md2)
    app_root.mainloop()
