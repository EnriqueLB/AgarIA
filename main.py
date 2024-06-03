import tkinter as tk
from tkinter import filedialog, Menu, ttk
from PIL import Image, ImageTk, ImageDraw, ImageEnhance
import webcolors
import cv2
import numpy as np
from tkinter import messagebox 
from collections import Counter

AGAR_TYPE = {
    "macconkey": "MacConkey", 
    "agarSalmonella": "Agar Salmonella", 
    "agarXLD": "Agar XLD",
}

COLOR_TRANSLATIONS = [
    {
        "agar": AGAR_TYPE["macconkey"],
        "bacteria": "E. Coli",
        "colors": ["indianred", "palevioletred", "pink", "hotpink", "lightpink", "plum"]
    },
     {
        "agar": AGAR_TYPE["macconkey"],
        "bacteria": "Proteus mirabilis",
        "colors": ["darkkhaki", "darksalmon", "rosybrown", "peru"]
    },
    {
        "agar": AGAR_TYPE["agarXLD"],
        "bacteria": "Proteus mirabilis",
        "colors": ["darkkhaki", "darksalmon", "rosybrown", "lightpink"]
    },
     {
        "agar": AGAR_TYPE["agarXLD"],
        "bacteria": "Salmonella",
        "colors": ["deeppink", "maroon", "black"]
    },
      {
        "agar": AGAR_TYPE["agarXLD"],
        "bacteria": "Shigella",
        "colors": ["lightpink", "brown", "indianred"]
    },
     {
        "agar": AGAR_TYPE["agarSalmonella"],
        "bacteria": "Salmonella Typhimurium",
        "colors": ["black"]
    }
]

class PhotoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Agar IA")
        self.root.state("zoomed")

        self.canvas = tk.Canvas(root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.image_original = None 
        self.tk_image = None
        self.crop_circle = None

        self.circle_start_x = None
        self.circle_start_y = None
        self.circle_end_x = None
        self.circle_end_y = None

        self.dragging = False
        self.resizing = False
        self.moving = False
        # self.image_history = []
        self.canvas.bind("<Button-1>", self.on_click)
        # self.canvas.bind("<Button-3>", self.capture_color)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Return>", self.replace_image)
        # self.root.bind("<Control-z>", self.undo)
        # self.root.bind("<Control-Z>", self.undo)
        
        self.setup_menu()

        self.combo = ttk.Combobox(root,
            state="readonly",
            values=[AGAR_TYPE for AGAR_TYPE in AGAR_TYPE.values()],
        )
        
        self.combo.current(0)
        self.combo.pack(side=tk.RIGHT, expand=True)
        self.sensitivity = tk.Scale(root, from_=0, to=10, orient=tk.HORIZONTAL, resolution=1, label="Sensitivity", command=self.update_se)
        self.sensitivity.set(1)
        self.sensitivity.pack(side=tk.RIGHT, expand=True)
        self.neighborhood = tk.Scale(root, from_=0, to=30, orient=tk.HORIZONTAL, resolution=1, label="Neighborhood", command=self.update_se)
        self.neighborhood.set(15)
        self.accumulator = tk.Scale(root, from_=1, to=50, orient=tk.HORIZONTAL, resolution=1, label="Accumulator", command=self.update_se)
        self.accumulator.set(15)
        self.accumulator.pack(side=tk.RIGHT, expand=True)
        self.minRadius = tk.Scale(root, from_=0, to=40, orient=tk.HORIZONTAL, resolution=1, label="Min Radius", command=self.update_se)
        self.minRadius.set(5)
        self.minRadius.pack(side=tk.RIGHT, expand=True)
        self.maxRadius = tk.Scale(root, from_=0, to=40, orient=tk.HORIZONTAL, resolution=1, label="Max Radius", command=self.update_se)
        self.maxRadius.set(15)
        self.maxRadius.pack(side=tk.RIGHT, expand=True)
        

        
    def open_custom_popup(self):
         
        def closePopup():
            if hasattr(self, "image_array"):
                self.image_edited = self.image_array.copy()
                self.image_array = np.array(self.image_original) 
            popup.destroy()
    # Crear una nueva ventana emergente
        popup = tk.Toplevel()
        popup.title("Custom Popup")
        popup.geometry("200x200")
        
        popup.protocol("WM_DELETE_WINDOW", closePopup)

        # Agregar un Scale a la ventana emergente
        label_texto = tk.Label(popup, text="Ajustar contraste")
        label_texto.pack()

        escalado = tk.Scale(popup, from_=-1.0, to=5.0, orient=tk.HORIZONTAL, label="Escalado", resolution=0.1)
        # escalado.set(1.0)
        escalado.pack(pady=10)
        desplazamiento = tk.Scale(popup, from_=-200.0, to=200.0, orient=tk.HORIZONTAL, label="Desplazamiento")
        # desplazamiento.set(100)
        desplazamiento.pack(pady=10)
        escalado.config(command= lambda x: self.ajustar_contraste(escalado.get(), desplazamiento.get()))
        desplazamiento.config(command= lambda x: self.ajustar_contraste(escalado.get(), desplazamiento.get()))

    
    def ajustar_contraste(self, alpha, beta):
        if not hasattr(self, "image_original") or not self.image_original:
            return
        self.image_array = np.array(self.image_original) 
        self.image_array = cv2.convertScaleAbs(self.image_array, alpha=alpha, beta=beta)
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(self.image_array))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
    
    
    def update_se(self, event = None):
        if not hasattr(self, "image_original") or not self.image_original:
            return
        
        self.image_array = np.array(self.image_original)
        
        def contar_circulos(circles):
            if circles is not None:
                circles = np.uint16(np.around(circles))
                colors = []
                for i in circles[0,:]:
                    try:
                        x, y, _ = i
                        color = self.image_array[y, x]  # Obtiene el color del píxel en el centro del círculo
                        colors.append(tuple(color))
                    except IndexError as e:
                        print("Error index:", e)
                    cv2.circle(self.image_array, (i[0], i[1]), i[2], (0, 0, 255), 2)
                # Encuentra el color predominante
                color_counts = Counter(colors)
                predominant_color = max(color_counts, key=color_counts.get)
                self.predominant_color = self.get_color_name(predominant_color[:3])
                return len(circles[0])
            return -1
        
        if not hasattr(self, "image_incolor"):
            
            gray = cv2.cvtColor(self.image_array if not hasattr(self, "image_edited") else self.image_edited, cv2.COLOR_BGR2GRAY)
            _, th2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            cv2.imshow("TH2", th2)
        
            while True:
                # Esperar 1 ms a que ocurra un evento de teclado
                key = cv2.waitKey(1) & 0xFF

                # Si se presiona la tecla Enter (clave 13)
                if key == 13:
                    print("Se presionó Enter")
                    self.image_incolor = th2
                    break

                # Si la ventana está cerrada (esto se detecta como que no se puede leer más cuadros)
                if cv2.getWindowProperty('TH2', cv2.WND_PROP_VISIBLE) < 1:
                    print("La ventana se cerró")
                    self.image_incolor = gray
                    break

            # Cerrar todas las ventanas
            cv2.destroyAllWindows()
            
        

        circles = cv2.HoughCircles(self.image_incolor, cv2.HOUGH_GRADIENT, self.sensitivity.get()+1, self.neighborhood.get()+1, param1=100, param2=self.accumulator.get()+1, minRadius=self.minRadius.get()+1, maxRadius=self.maxRadius.get()+1)

        self.finished = contar_circulos(circles)        
        
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(self.image_array))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
   
    
    def setup_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.load_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_image,  accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit,  accelerator="Ctrl+X")
        
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Filtros", command=self.open_custom_popup)
        edit_menu.add_command(label="Redo",)
        self.root.bind("<Control-o>", self.load_image)
        self.root.bind("<Control-s>", self.save_image)
        self.root.bind("<Control-x>", self.root.quit)

        
    def save_image(self):
        if self.image_original:
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
            if file_path:
                self.image.save(file_path)
           

                 
    # def undo(self, event):
    #     if self.image_history:
    #         self.image = self.image_history.pop()
    #         self.tk_image = ImageTk.PhotoImage(self.image)
    #         self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
    #         self.crop_circle = None
    #         self.finished = False
            
    def load_image(self, event=None):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image_original = Image.open(file_path)
            # Verifica el tamaño del canvas
            canvas_width, canvas_height = self.canvas.winfo_width(), self.canvas.winfo_height()
            image_width, image_height = self.image_original.size

            # Si la imagen es más grande que el canvas, redimensiona
            if image_width > canvas_width or image_height > canvas_height:
                # Calcula la relación de aspecto
                ratio_width = canvas_width / image_width
                ratio_height = canvas_height / image_height
                ratio = min(ratio_width, ratio_height)  # Usar el ratio menor para asegurar que cabe en el canvas

                # Nuevo tamaño de la imagen
                new_width = int(image_width * ratio)
                new_height = int(image_height * ratio)

                # Redimensiona la imagen
                self.image_original = self.image_original.resize((new_width, new_height), Image.BILINEAR)


            self.tk_image = ImageTk.PhotoImage(self.image_original)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            # self.image_history.append(self.image_original.copy())
          

    def on_click(self, event):
        if not self.image_original:
            return
        x, y = event.x, event.y
        if self.crop_circle and self.is_inside_circle(x, y):
            self.moving = True
            self.move_start_x = x
            self.move_start_y = y
        elif self.crop_circle and self.is_on_border(x, y):
            self.resizing = True
            self.resize_start_x = x
            self.resize_start_y = y
        else:
            self.dragging = True
            self.circle_start_x = x
            self.circle_start_y = y
            self.circle_end_x = x
            self.circle_end_y = y

    def on_drag(self, event):
        x, y = event.x, event.y
        if self.dragging:
            self.circle_end_x = x
            self.circle_end_y = y
            if self.crop_circle:
                self.canvas.delete(self.crop_circle)
            self.crop_circle = self.canvas.create_oval(self.circle_start_x, self.circle_start_y, self.circle_end_x, self.circle_end_y, outline='red')
        elif self.resizing:
            self.circle_end_x = x
            self.circle_end_y = y
            self.canvas.delete(self.crop_circle)
            self.crop_circle = self.canvas.create_oval(self.circle_start_x, self.circle_start_y, self.circle_end_x, self.circle_end_y, outline='red')
        elif self.moving:
            dx = x - self.move_start_x
            dy = y - self.move_start_y
            self.canvas.move(self.crop_circle, dx, dy)
            self.circle_start_x += dx
            self.circle_start_y += dy
            self.circle_end_x += dx
            self.circle_end_y += dy
            self.move_start_x = x
            self.move_start_y = y

    def on_release(self, event):
        self.dragging = False
        self.resizing = False
        self.moving = False
        if self.crop_circle:
                self.x1, self.y1, self.x2, self.y2 = self.canvas.coords(self.crop_circle)


    def is_inside_circle(self, x, y):
        x1, y1, x2, y2 = self.canvas.coords(self.crop_circle)
        radius = (x2 - x1) / 2
        center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
        return (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2
    
    def is_on_border(self, x, y):
        x1, y1, x2, y2 = self.canvas.coords(self.crop_circle)
        border_threshold = 10
        return (x1 - border_threshold <= x <= x1 + border_threshold or
                x2 - border_threshold <= x <= x2 + border_threshold or
                y1 - border_threshold <= y <= y1 + border_threshold or
                y2 - border_threshold <= y <= y2 + border_threshold)

    def crop_image(self, x1, y1, x2, y2):
        if self.image_original:
            diameter = min(x2 - x1, y2 - y1)
            mask = Image.new('L', (diameter, diameter), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, diameter, diameter), fill=255)

            self.cropped_image = self.image_original.crop((x1, y1, x1 + diameter, y1 + diameter))
            if hasattr(self, "image_edited"):
                temp_image = Image.fromarray(self.image_edited)
                temp_edited = temp_image.crop((x1, y1, x1 + diameter, y1 + diameter))
                self.image_edited = np.array(temp_edited)
                
                print("recorte aplicado")
            self.cropped_image.putalpha(mask)
            
            # result = Image.new('RGBA', (diameter, diameter))
            # result.paste(cropped_image, (0, 0), mask)
            # result.show()
            
    def replace_image(self, event):
        if hasattr(self, 'finished') and self.finished:
            bacteria = "No definida"
            for x in COLOR_TRANSLATIONS:
                if self.combo.get() == x["agar"] and self.predominant_color in x["colors"]:
                    bacteria = x["bacteria"]
                    break
            messagebox.showinfo("Resultado", f"Cantidad de colonias encontradas: {self.finished}\nColor dominante: {self.predominant_color}\nBacteria: {bacteria}") 
            # messagebox.showinfo("Resultado", f"Cantidad de colonias encontradas: {self.finished}\nBacteria: {bacteria}") 
            return
        self.crop_image(int(self.x1), int(self.y1), int(self.x2), int(self.y2))
        self.canvas.delete(self.crop_circle)
        
        if self.cropped_image:
            # self.image_history.append(self.cropped_image.copy())
            self.image_original = self.cropped_image
            self.tk_image = ImageTk.PhotoImage(self.image_original)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))  # Update the scroll region
            self.cropped_image = None  # Reset the cropped image
            self.update_se()

            # print(self.get_dominant_and_least_color_name())
            
        

    def get_dominant_and_least_color(self, num_colors=10):
        if self.image_original:
            image = self.image_original.convert('P', palette=Image.ADAPTIVE, colors=num_colors)
            palette = image.getpalette()
            color_counts = sorted(image.getcolors(), reverse=True)
            dominant_color_index = color_counts[0][1]
            least_color_index = color_counts[-1][1]
            dominant_color = palette[dominant_color_index*3:dominant_color_index*3+3]
            least_color = palette[least_color_index*3:least_color_index*3+3]
            return tuple(dominant_color), tuple(least_color)
        else:
            return None, None

    def get_dominant_and_least_color_name(self):
        dominant_color, least_color = self.get_dominant_and_least_color()
        if dominant_color and least_color:
            dominant_color_name = self.get_color_name(dominant_color)
            least_color_name = self.get_color_name(least_color)
            return dominant_color_name, least_color_name
        else:
            return None, None

    def get_color_name(self, rgb_color):
        try:
            closest_name = webcolors.rgb_to_name(rgb_color)
        except ValueError:
            closest_name = self.closest_color(rgb_color)
        return closest_name

    def closest_color(self, requested_color):
        min_colors = {}
        for hex_code, name in webcolors.CSS3_HEX_TO_NAMES.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(hex_code)
            rd = (r_c - requested_color[0]) ** 2
            gd = (g_c - requested_color[1]) ** 2
            bd = (b_c - requested_color[2]) ** 2
            min_colors[(rd + gd + bd)] = name
        return min_colors[min(min_colors.keys())]
        
if __name__ == "__main__":
    root = tk.Tk()
    editor = PhotoEditor(root)
    root.mainloop()
