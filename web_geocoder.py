from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
from geopy.geocoders import ArcGIS
import folium

ArcGIS().timeout = 1000

app = Flask(__name__)

mapurl_dict = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/uploaded_sucessfully.html', methods = ['POST', 'GET'])
def uploaded():
    global file_out_name

    if request.method == 'POST':
        uploaded = request.files.to_dict()
        file_in = uploaded['uploaded_file']

        file_in_name = secure_filename('uploaded_{}_{}'.format(datetime.now().strftime('%Y%m%d%H%M%S'), file_in.filename))
        file_in.save(file_in_name)

        if file_in.filename[-3:] == 'csv':
            df = pd.read_csv(file_in_name)

        if file_in.filename[-4:] == 'xlsx':
            df = pd.read_excel(file_in_name, sheet_name = 0)

        if 'Unnamed: 0' in df.columns:
            df = df.drop('Unnamed: 0', 1)
        df['_ID'] = list(range(1, len(df)+1))
        df.set_index('_ID', inplace = True)

        if any(c.lower() in ['address', 'add', 'addresses'] for c in df.columns):
            file_out_name = 'geocoded_{}'.format(file_in_name)

            for c in df.columns:
                if c.lower() in ['address', 'add', 'addresses']:
                    df['longitude'] = [ArcGIS().geocode(i, timeout = 1000).longitude for i in df[c]]
                    df['latitude'] = [ArcGIS().geocode(i, timeout = 1000).latitude for i in df[c]]
                    if file_in.filename[-3:] == 'csv':
                        df.to_csv(file_out_name)
                    if file_in.filename[-4:] == 'xlsx':
                        df.to_excel(file_out_name)

                    df['map'] = ['show map'] * len(df)

                    df_html_0 = df.to_html().replace('NaN', '').replace("<th>_ID</th>", "<th></th>").replace("dataframe", "results_table")


                    df_html_dict = {}
                    df_html_dict[0] = df_html_0
                    for i in range(1, len(df)+1):
                        map = folium.Map(location = [df.latitude[i], df.longitude[i]], zoom_start = 6, tiles = 'Stamen Terrain')
                        map.add_child(folium.Marker(location = [df.latitude[i], df.longitude[i]], popup = folium.Popup(df[c][i], parse_html = True), icon = folium.Icon(color = 'blue')))
                        map.save('./templates/map{}.html'.format(i))

                        map_html = open('./templates/map{}.html'.format(i), 'r+')
                        map_html.seek(101)
                        map_html.write("""<link rel="icon" href="./static/assets/favicon.ico"><script>\n""")

                        map_url = 'lat={}&lng={}.html'.format(df.latitude[i], df.longitude[i])
                        mapurl_dict[map_url] = 'map{}.html'.format(i)
                        df_html_dict[i] = df_html_dict[i-1].replace('<td>show map</td>', "<td><a target='_blank' href='/{}'>show map</a></td>".format(map_url), 1)


                    map2 = folium.Map(location = [df.latitude[1], df.longitude[1]], zoom_start = 4, tiles = 'Stamen Terrain')
                    fg = folium.FeatureGroup(name = 'all_add')
                    for i in range(1, len(df)+1):
                        fg.add_child(folium.Marker(location = [df.latitude[i], df.longitude[i]], popup = folium.Popup(df[c][i], parse_html = True), icon = folium.Icon(color = 'blue')))
                    map2.add_child(fg)
                    map2.save('./templates/all_map.html')

                    map2_html = open('./templates/all_map.html', 'r+')
                    map2_html.seek(101)
                    map2_html.write("""<link rel="icon" href="./static/assets/favicon.ico"><script>\n""")

                    map2_url = 'all=True&filename={}'.format(file_out_name)
                    mapurl_dict[map2_url] = 'all_map.html'

                    return render_template('valid.html', filename = file_out_name, table = df_html_dict[len(df)], all_in_map = '/{}'.format(map2_url))

        else:
            return render_template('invalidupload.html')
    else:
        return 'Something went wrong. Please try again!'

@app.route('/example.html')
def example():
    return render_template('fileexample.html')

@app.route('/download.html', methods = ['POST', 'GET'])
def downloaded():
    if request.method == 'POST':
        return send_file(file_out_name, as_attachment = True, attachment_filename = file_out_name)
    else:
        return 'Something went wrong. Please try again!'

@app.route('/<string:map_url>')
def map(map_url):
    return render_template(mapurl_dict[map_url])

if __name__ == '__main__':
    app.run(debug = True)
