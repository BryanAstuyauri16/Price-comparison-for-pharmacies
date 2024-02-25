from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import time
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np

from dash import Dash, dash_table, dcc, html, callback, clientside_callback
import dash_bootstrap_components as dbc
from dash.dependencies import State, Input, Output

import warnings
def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings(action="ignore"):
    fxn()

###
class Pharmacy_data():

    def __init__(self, url, pharmacy, product):
        self.url= url
        self.product= product
        self.pharmacy= pharmacy

    def initialize(self):
        options = Options()
        options.add_argument('--headless=new')

        wd = webdriver.Chrome(options=options)
        wd.maximize_window()
        wd.get(self.url)
        time.sleep(15)
        wait = WebDriverWait(wd, timeout=15) 
        wait.until(EC.presence_of_element_located((By.XPATH, '//input[contains(@placeholder, "Busca")]'))) 
        Product = self.product
        Search_input = wd.find_element(By.XPATH, '//input[contains(@placeholder, "Busca")]')
        Search_input.send_keys(Product, Keys.RETURN)
        time.sleep(8)
        # wd.implicitly_wait(15)
        # wait = WebDriverWait(wd, timeout=10) 
        # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'fp-product-large span.product-name.text'))) 
        last_height = wd.execute_script("return document.body.scrollHeight")
        while True:
            wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # wd.implicitly_wait(10)
            time.sleep(3)
            new_height = wd.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        source= wd.page_source
        page= BeautifulSoup(source, 'html.parser')
        wd.close()
        wd.quit()
        return page
    def get_data(self):
        df= pd.DataFrame()
        page= self.initialize()
        Products= page.select('div.col-12.col-sm-6.col-lg-4.col-xxl-3.mb-3.ng-star-inserted')
        if self.pharmacy ==  'Inkafarma':
            for product in Products:
                Product_name= product.select('fp-product-large span.product-name.text')[0].text
                Actual_price= product.select('fp-product-large fp-product-price>p:nth-child(2)')[0].text
                Regular_price= product.select('fp-product-large fp-product-regular-price.ng-star-inserted')
                if Regular_price == []:
                    Regular_price= Actual_price
                else:
                    Regular_price= Regular_price[0].text

                Price_dsct= product.select('fp-product-large div.text-left.flex-grow-1:first-child')
                if Price_dsct == []:
                    Price_dsct= 'No hay descuento'
                else:
                    Price_dsct= Price_dsct[0].text

                Prd_link= self.url + product.select('fp-product-large div fp-link a')[0].get('href')
                Size= product.select('fp-product-large span.text-tag')[0].text
                img_src= product.select('fp-product-large div.col-12.display-center fp-lazy-wrapper>img')[0].get('src')
                row = pd.DataFrame(data= {'Nombre del Producto': [Product_name], 'Size': [Size], f'Actual Price {self.pharmacy[0]}': [Actual_price], f'Regular Price {self.pharmacy[0]}': [Regular_price], f'Price Dsct {self.pharmacy[0]}': [Price_dsct], 'Source': [img_src], 'Prd_link': [Prd_link]})
                df = pd.concat([df, row], axis = 0)
        
        if self.pharmacy == 'Mifarma':
            for product in Products:
                Product_name= product.select('fp-product-large span.product-name.text')[0].text
                Regular_price= product.select('fp-product-large fp-product-regular-price-mifa div div:first-child span')[0].text
                Actual_price= product.select('fp-product-large fp-product-price-mifa div div span')[0].text
                if Actual_price == '\xa0':
                    Actual_price= Regular_price
                Price_dsct= product.select('fp-product-large fp-product-offer-price-mifa div div p')
                if Price_dsct == []:
                    Price_dsct= 'No hay descuento'
                else:
                    Price_dsct= Price_dsct[0].text
                Prd_link= self.url + product.select('fp-product-large div fp-link a')[0].get('href')
                Size= product.select('fp-product-large span.text-tag')[0].text
                img_src= product.select('fp-product-large div.col-12.display-center fp-lazy-wrapper>img')[0].get('src')
                row = pd.DataFrame(data= {'Nombre del Producto': [Product_name], 'Size': [Size], f'Actual Price {self.pharmacy[0]}': [Actual_price], f'Regular Price {self.pharmacy[0]}': [Regular_price], f'Price Dsct {self.pharmacy[0]}': [Price_dsct], 'Source': [img_src], 'Prd_link': [Prd_link]})
                df = pd.concat([df, row], axis = 0)

        df = df.reset_index(drop= True)
        return df          
   
###

def MI_data(product):
    urlM= 'https://www.mifarma.com.pe/'
    urlI= 'https://inkafarma.pe/'  
    data_M= Pharmacy_data(url= urlM, product= product, pharmacy= 'Mifarma').get_data()
    data_I= Pharmacy_data(url= urlI, product= product, pharmacy= 'Inkafarma').get_data()
    df= data_M.merge(data_I, on= ['Product Name', 'Size', 'Source'], how= 'inner').reset_index().rename(columns= {'index': 'id'})
    df= df.reset_index().rename(columns= {'index': 'ID'})
    df['ID']+= 1
    return df

def initial_df(No= 16):
    cols = (['Nombre del Producto'])
    data = np.repeat('Product Name', No)
    df = pd.DataFrame(data= data, columns= cols).reset_index().rename(columns= {'index': 'id'})
    df = df.reset_index().rename(columns= {'index': 'ID'})
    df['ID'] += 1
    return df

###
    
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
server= app.server

title= dbc.Row(dbc.Col(html.Div(
    html.H1("Comparación de precios entre productos de Mifarma e Inkafarma", className= 'pt-2')),
    style= dict(display= 'flex', justifyContent= 'center')
    ), class_name= 'border border-dark', style= {'backgroundColor':'rgb(255, 178, 102)'},
    )

#Left
inputrow= dbc.Row(
    dbc.Col([
        html.H6("Ingrese un valor y presione submit: ", className= 'pt-2 pe-2'),
        dcc.Input(id= 'input_submit', type= 'text', placeholder= "Ingrese un producto", className= 'my-1'),
        html.Button('Submit', id='submit-val', n_clicks=0, className= 'my-1'),
    ], style= dict(display='flex', justifyContent='center', height= '6vh')),
    className= 'pb-1'
    # style= dict(height= '6vh')
    )
table= html.Div(dbc.Col([
    dbc.Row(html.Div(
        dash_table.DataTable(
            id='datatable-interactivity',
            data= []
        ), style= {'height': '68vh'}), style= {"overflow": "scroll"}, class_name= 'border border-dark mt-1'),
    dbc.Row(dbc.Alert(html.Small(html.Small(id='tbl_out'))), style= {'height': '12vh'}),
], width= 12, style= {'backgroundColor':'rgb(224, 224, 224)', 'height': '80vh'}))

#Right
prdt= dbc.Row([
    dbc.Row(html.H4("Detalles del producto", style= {'display': 'flex', 'justifyContent': 'center', 'height': '6vh'})),
    dbc.Row([
        dbc.Col([
            dbc.Row(html.H5(html.B("Mifarma", style= dict(display= 'flex', justifyContent= 'center', className="h-50")))),
            dbc.Row(html.Small(html.B('Precio regular', style= dict(display= 'flex', justifyContent= 'center')))),
            dbc.Row(html.Small(html.B(html.Small(style= dict(display= 'flex', justifyContent= 'center'), id= 'PRM')))),
            dbc.Row(html.Small(html.B('Precio actual', style= dict(display= 'flex', justifyContent= 'center')))),
            dbc.Row(html.Small(html.B(html.Small(style= dict(display= '    flex', justifyContent= 'center'), id= 'PAM')))),
            dbc.Row(html.Small(html.B('Precio en dscto', style= dict(display= 'flex', justifyContent= 'center')))),
            dbc.Row(html.Small(html.B(html.Small(style= dict(display= 'flex', justifyContent= 'center'), id= 'PDM')))),
            dbc.Row(html.A(html.Img(src= "https://www.logotypes101.com/logos/895/91CD772F37464645C2EF582E2197ADC9/mi_farma.png", className= 'pt-2 pb-2', style=dict(display='flex', justifyContent='center', width= '100%', height= '100%')), href= 'https://www.mifarma.com.pe/'), className= 'pt-2'),
            dbc.Row(html.Small(html.B("Contacto")), className= 'pt-3'),
            dbc.Row([
                dbc.Col(html.A([html.Img(src= "https://png.pngtree.com/png-vector/20221018/ourmid/pngtree-whatsapp-phone-icon-png-image_6315989.png", style=dict(display='flex', justifyContent='center', width= '7vh', height= '7vh'), className= 'mt-1')], href= 'https://api.whatsapp.com/send?phone=51997539651')),      
                dbc.Col(html.A([html.Img(src= "https://plus.unsplash.com/premium_photo-1679513691474-73102089c117?w=400&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NDF8fGhlYWRwaG9uZXN8ZW58MHx8MHx8fDA%3D", style=dict(display='flex', justifyContent='center', width= '7vh', height= '7vh'), className= 'mt-1')], href= 'tel:016125000')),      
            ]),
            dbc.Row(html.Small(html.B("Retiro en tienda")), className= 'pt-3'),
            dbc.Row([
                dbc.Col(html.A([html.Img(src= "https://images.unsplash.com/photo-1472851294608-062f824d29cc?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", style=dict(display='flex', justifyContent='center', width= '100%', height= '100%'), className= 'pb-1')], href= 'https://www.mifarma.com.pe//informativo/retiro-en-botica')),      
            ]),
        ], width= 3, style= {'backgroundColor':'rgb(224, 224, 224)'}, class_name= 'border border-dark pt-4'),
        dbc.Col([
            html.Img(style=dict(display='flex', justifyContent='center', width= '100%', height= '37.5vh'), id= 'img'),
            html.Small(html.B("Desmaquillante de Cara y Ojos Sensyses Cleanse...	", id= 'PGD')),
            dbc.Row([
                dbc.Row(html.H4('Detalles adicionales', style= dict(display= 'flex', justifyContent= 'center'))),
                dbc.Row([html.P(html.Small(html.Small('"Precio en dscto" se refiere a productos en descuentos con tarjeta oh! Si desea acceder al producto simplemente haga click en la farmacia a la cual desee acceder debajo')))], style= dict(display= 'flex', justifyContent= 'center')), 
            ]),
            dbc.Row([
                dbc.Row(html.A(html.P(html.Small(html.Small(html.B('Mifarma'))), style= dict(display= 'flex', justifyContent= 'center')), href= 'https://www.mifarma.com.pe/buscador?keyword=bloqueador', id= 'I_Product_link')),
                dbc.Row(html.A(html.P(html.Small(html.Small(html.A(html.B('Inkafarma')))), style= dict(display= 'flex', justifyContent= 'center', )), href= 'https://www.mifarma.com.pe/buscador?keyword=bloqueador', id= 'M_Product_link')),
            ])
        ], width=6, style= dict(backgroundColor= 'rgb(224, 224, 224)'), class_name= 'border border-dark pt-2'),
        dbc.Col([
            dbc.Row(html.H5(html.B("Inkafarma", style= dict(display= 'flex', justifyContent= 'center', className= 'pt-5')))),
            dbc.Row(html.Small(html.B('Precio regular', style= dict(display= 'flex', justifyContent= 'center')))),
            dbc.Row(html.Small(html.B(html.Small(style= dict(display= 'flex', justifyContent= 'center'), id= 'PRI')))),
            dbc.Row(html.Small(html.B('Precio actual', style= dict(display= 'flex', justifyContent= 'center')))),
            dbc.Row(html.Small(html.B(html.Small(style= dict(display= '    flex', justifyContent= 'center'), id= 'PAI')))),
            dbc.Row(html.Small(html.B('Precio en dscto', style= dict(display= 'flex', justifyContent= 'center')))),
            dbc.Row(html.Small(html.B(html.Small(style= dict(display= 'flex', justifyContent= 'center'), id= 'PDI')))),
            dbc.Row(html.A(html.Img(src= "https://m.openplaza.com.pe/sites/default/files/Peru/Pucallpa/Tiendas/Logos/INKA%20FARMA.jpg", className= 'pt-2 pb-2', style=dict(display='flex', justifyContent='center', width= '100%', height= '100%')), href= 'https://inkafarma.pe/'), className= 'pt-2'),
            dbc.Row(html.Small(html.B("Contacto")), className= 'pt-3'),
            dbc.Row([
                dbc.Col(html.A([html.Img(src= "https://png.pngtree.com/png-vector/20221018/ourmid/pngtree-whatsapp-phone-icon-png-image_6315989.png", style=dict(display='flex', justifyContent='center', width= '7vh', height= '7vh'), className= 'mt-1')], href= 'https://inkafarma.pe/informativo/aliviamed')),      
                dbc.Col(html.A([html.Img(src= "https://plus.unsplash.com/premium_photo-1679513691474-73102089c117?w=400&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NDF8fGhlYWRwaG9uZXN8ZW58MHx8MHx8fDA%3D", style=dict(display='flex', justifyContent='center', width= '7vh', height= '7vh'), className= 'mt-1')], href= 'tel:013142020')),      
            ]),
            dbc.Row(html.Small(html.B("Retiro en tienda")), className= 'pt-3'),
            dbc.Row([
                dbc.Col(html.A([html.Img(src= "https://images.unsplash.com/photo-1472851294608-062f824d29cc?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D", style=dict(display='flex', justifyContent='center', width= '100%', height= '100%'), className= 'pb-1')], href= 'https://inkafarma.pe/consultastock/afiliacion')),      
            ]),
        ], width= 3, style= {'backgroundColor':'rgb(224, 224, 224)'}, class_name= 'border border-dark pt-4'),
    ], style= {'display': 'flex', 'justifyContent': 'center', 'height': '80vh'}),
])


columns= dbc.Row([
    dbc.Col([inputrow, table], width= 6, className= 'ps-5 pt-2'),
    dbc.Col([prdt], width= 6, className= 'ps-5 pt-2')
], style= dict(backgroundColor= 'rgb(192, 192, 192)'))

app.layout= dbc.Container(
    [
    title,
    columns,
], fluid= True, style= dict(height= '100vh')
)

@callback(
    Output("datatable-interactivity", "data"), Output("datatable-interactivity", "columns"), Output('tbl_out', 'children'), Output("datatable-interactivity", "style_data_conditional"), Output("datatable-interactivity", "style_header_conditional"), Output("datatable-interactivity", "style_table"), Output("datatable-interactivity", "filter_action"), Output("datatable-interactivity", "sort_action"), Output("datatable-interactivity", "page_size"),
    Input("submit-val", "n_clicks"),
    State("input_submit", "value"),
)
def Update_dataTable(n_clicks, product):
    if n_clicks > 0:
        inicio = time.time()
        product= product.lower()
        global df
        df= MI_data(product= product)
        columns = [
            {"name": i, "id": i} for i in df.columns if (i == 'Product Name') | (i == 'ID') #this leads df
        ]
        fin = time.time()
        time_taken= "%.1f" % (fin- inicio)
        Alert= f'Tu tabla ha sido actualizada. Se encontraron {df.index[-1]+ 1} productos coincidentes relacionados a {product} en {time_taken} segundos. Haga click en la tabla para visualizar los detalles.'
        style_data_conditional= [
            {
                'if': {
                    'row_index': 'odd'
                },
                'backgroundColor': 'rgb(30, 30, 30)',
                'color': 'white',
                'textOverflow': 'ellipsis',
                'overflow': 'hidden',
                'text-align': 'left',
            },
            {
                'if': {
                    'row_index': 'even'
                },
                'backgroundColor': 'rgb(220, 220, 220)',
                'textOverflow': 'ellipsis',
                'overflow': 'hidden',
                'text-align': 'left',
            },
            {
                'if': {
                    'column_id': 'ID'
                },
                'text-align': 'center',
                'width': '75px'
            }
        ] #not come here!!!
        style_header_conditional= [
            {
                'if': {
                    'column_id' : ['Nombre del Producto', 'ID']
                },
                'backgroundColor': 'rgb(30, 30, 30)',
                'text-align': 'center',
                'color': 'white',
            }
        ]
        style_table= {"overflowX": "auto",
                     'minWidth': '100%'}
        filter_action="native"
        sort_action="native"
        page_size= 12
        # page_current= 0  ##default
        # page_action= 'native' ##default
        # style= {'height': '12vh'}
    else:
        df = initial_df()
        columns = [
                {"name": i, "id": i} for i in df.columns if i != 'id'
            ]
        Alert= f'Ingrese un valor y presione submit para ver los detalles de la data obtenida.'
        style_data_conditional= [
            {
                'if': {
                    'row_index': 'odd'
                },
                'backgroundColor': 'rgb(30, 30, 30)',
                'color': 'white',
                'textOverflow': 'ellipsis',
                'overflow': 'hidden',
                'text-align': 'left',
            },
            {
                'if': {
                    'row_index': 'even'
                },
                'backgroundColor': 'rgb(220, 220, 220)',
                'textOverflow': 'ellipsis',
                'overflow': 'hidden',
                'text-align': 'left',
            },
            {
                'if': {
                    'column_id': 'ID'
                },
                'text-align': 'center',
                'width': '75px'
            }
        ] #not come here!!!
        style_header_conditional= [
            {
                'if': {
                    'column_id' : ['Nombre del Producto', 'ID']
                },
                'backgroundColor': 'rgb(30, 30, 30)',
                'text-align': 'center',
                'color': 'white',
            }
        ]
        style_table= {"overflowX": "auto",
                     'minWidth': '100%'}
        filter_action="native"
        sort_action="native"
        page_size= 12

    return df.to_dict('records'), columns, Alert, style_data_conditional, style_header_conditional, style_table, filter_action, sort_action, page_size

@callback(
    Output('PRM', 'children'), Output('PAM', 'children'), Output('PDM', 'children'), Output('PRI', 'children'), Output('PAI', 'children'), Output('PDI', 'children'), Output('PGD', 'children'), Output('I_Product_link', 'href'), Output('M_Product_link', 'href'), Output('img', 'src'),
    Input('datatable-interactivity', 'active_cell')
)
def Update_product_details(active_cell):
    imagen= 'https://images.unsplash.com/photo-1682687220777-2c60708d6889?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDF8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
    if active_cell:
        row= int(active_cell['row_id'])
        pam= df['Actual Price M'][row]
        pai= df['Actual Price I'][row]

        pdm= df['Price Dsct M'][row]
        pdi= df['Price Dsct I'][row]

        prm= df['Regular Price M'][row]
        pri= df['Regular Price I'][row]

        pgd= df['Product Name'][row] + " - " + (df['Size'][row])

        Prd_link_x= df['Prd_link_x'][row]
        Prd_link_y= df['Prd_link_y'][row]

        imagen = df['Source'][row]

        return prm, pam, pdm, pri, pai, pdi, pgd, Prd_link_x, Prd_link_y, imagen
    else:
        pam= "S/ 00.00"
        pai= "S/ 00.00"

        pdm= "S/ 00.00"
        pdi= "S/ 00.00"

        prm= "S/ 00.00"
        pri= "S/ 00.00"

        pgd= "Desmaquillante de Cara y Ojos Sensyses Cleanse...	"

        Prd_link_x= ""
        Prd_link_y= ""

        return prm, pam, pdm, pri, pai, pdi, pgd, Prd_link_x, Prd_link_y, imagen

if __name__ == '__main__':
    app.run(debug= True)
