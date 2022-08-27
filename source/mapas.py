from turtle import fillcolor
import geopandas as gpd
import plotly.graph_objects as go
import json
import streamlit as st
import pandas as pd
import numpy as np
import os

#cwd = os.chdir('/Users/jaimevarelap/Documents/ITAM/Servicio Social/DATALAB/mapas')

# Agrupamos por municipio y tipo de tecnología los datos del IFT
ift = pd.read_csv('./TD_ACC_BAF_ITE_VA.csv')
ift = ift.drop(columns=['ENTIDAD','FECHA','TECNO_ACCESO_INTERNET','CONCESIONARIO','EMPRESA','K_GRUPO','GRUPO','ENTIDAD','MUNICIPIO'])
ift = ift[ift['ANIO']==2021]
ift = ift[ift['MES']==6]
ift = ift.dropna(subset=['A_TOTAL_E'])
ift['A_TOTAL_E'] = ift['A_TOTAL_E'].replace(',','',regex=True).astype('int64')
ift = ift.groupby(['K_ENTIDAD','K_MUNICIPIO','K_ACCESO_INTERNET'],as_index=False)["A_TOTAL_E"].sum()
ift = ift.rename(columns={"K_ENTIDAD":"CVE_ENT","K_MUNICIPIO":"CVE_MUN"})
#print(ift)

# Leemos shapefile de municipios
municipios = gpd.read_file('./municipios/municipios.shx')
municipios.crs = "EPSG:4326"
municipios = municipios.drop(columns=['CVEGEO','NOM_ENT','AREA','PERIMETER','NOM_MUN','COV_'])
municipios['CVE_ENT'] = municipios['CVE_ENT'].astype('int64')
municipios['CVE_MUN'] = municipios['CVE_MUN'].astype('int64')
municipios['zeros'] = np.zeros((len(municipios)))

# Hacemos merge con las distintas tecnologías
tecnologias = ['CABLE_COAXIAL','DSL','FIBRA_OPTICA','TECNOLOGIA_MOVIL']
i = 0
for t in [1,2,3,15]:
    ift_tecnologia = ift[ift['K_ACCESO_INTERNET']==t]
    ift_tecnologia = ift_tecnologia.rename(columns={"A_TOTAL_E": tecnologias[i]})
    ift_tecnologia = ift_tecnologia.drop(columns=['K_ACCESO_INTERNET'])
    municipios = municipios.merge(ift_tecnologia, how='left', on=['CVE_ENT','CVE_MUN'])
    i = i+1

# Hacemos merge con los datos de México Conectado
mc = pd.read_csv('./mexico_conectado.csv')
mc = mc[mc['STATUS']=='OPERANDO']
mc = mc.drop(columns=['STATUS','EMPRESA','N�MERO INTERIOR','VSATID','N�MERO EXTERIOR','LICITACION','ESTADO','MUNICIPIO','CLAVE_LOCALIDAD','LOCALIDAD','TIPO DE VIALIDAD','NOMBRE DE CALLE','NOMBRE DE COLONIA O BARRIO','CLAVE_CENTRO','NOMBRE_CENTRO','CLAVE_INMUEBLE','DEPENDENCIA','DEPENDENCIA/ENTIDAD_ESPECIFICA'])


#print(mc)
#print(mc.describe())

# Definimos los mapas
print("MAPEANDO...")
THRESHHOLD = 10
data = []

for tecnologia in tecnologias:
    municipios_tecnologia = municipios[municipios[tecnologia]>THRESHHOLD].set_index("COV_ID")
    #municipios_tecnologia = municipios[municipios[tecnologia]>THRESHHOLD][0:10].set_index("COV_ID")

    data.append(
        go.Choroplethmapbox(
            geojson = json.loads(municipios_tecnologia.to_json()),
            locations = municipios_tecnologia.index,
            z = municipios_tecnologia['zeros'],
            colorscale = 'spectral',
            showscale = False,
            zmin = -10,
            zmax = 1,
            selectedpoints = municipios_tecnologia['zeros'],
            unselected_marker_opacity = 0.5,
            visible = False
        )
    )

data.append(
    go.Scattermapbox(
        lat = mc['LAT'],
        lon = mc['LOG'],
        mode = 'markers',
        marker=go.scattermapbox.Marker(
            size=2,
            opacity = 1,
            color = '#ff7f0e',
        ),
        visible = False
    )
)

layout = go.Layout(
                mapbox_style="carto-positron",
                height = 800,
                autosize=True,
                mapbox = dict(center= dict(lat=23.5, lon= -102),zoom=4.3)
            )

layout.update(
    updatemenus = list([
        dict(
            x=-0.05,
            y=1,
            yanchor='top',
            showactive = True,
            buttons = list([
                dict(
                    args=['visible',[True,False,False,False,False]],
                    label = 'Cable Coaxial',
                    method = 'restyle'
                ),
                dict(
                    args=['visible',[False,True,False,False,False]],
                    label = 'DSL',
                    method = 'restyle'
                ),
                dict(
                    args=['visible',[False,False,True,False,False]],
                    label = 'Fibra Óptica',
                    method = 'restyle'
                ),
                dict(
                    args=['visible',[False,False,False,True,False]],
                    label = 'Tecnologia Móvil',
                    method = 'restyle'
                ),
                dict(
                    args=['visible',[False,False,False,False,True]],
                    label = 'Puntos México Conectado',
                    method = 'restyle'
                ),
            ])
        )
    ])
)

layout.update(
    title=dict(
        text = 'Acceso a internet',
        font = dict(
            size = 45
        )
    )
)

fig = go.Figure(data=data,layout=layout)
#fig.show()
fig.write_html("./mapa.html")