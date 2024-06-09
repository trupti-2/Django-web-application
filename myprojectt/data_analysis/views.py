from django.shortcuts import render, redirect
from django.conf import settings
from .forms import UploadFileForm
import pandas as pd
import os
import matplotlib.pyplot as plt
import io
import base64
import urllib

def handle_uploaded_file(f):
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f.name)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return file_path

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_path = handle_uploaded_file(request.FILES['file'])
            return redirect('data_analysis:analyze_file', file_path=file_path)
    else:
        form = UploadFileForm()
    return render(request, 'data_analysis/upload.html', {'form': form})

def analyze_file(request, file_path):
    try:
        # Ensure the file path is absolute
        if not os.path.isabs(file_path):
            file_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # Read the CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Generate HTML tables for data display
        first_rows = df.head().to_html()
        summary_stats = df.describe().to_html()
        
        # Convert the Series to a DataFrame for `to_html`
        missing_values = df.isnull().sum().to_frame('Missing Values').to_html()

        # Generate histogram for numerical columns
        plt.figure()
        df.hist()
        plt.tight_layout()

        # Save the plot to a PNG image
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = urllib.parse.quote(string)

        context = {
            'first_rows': first_rows,
            'summary_stats': summary_stats,
            'missing_values': missing_values,
            'plot_uri': uri,
        }
        return render(request, 'data_analysis/analyze.html', context)
    except FileNotFoundError:
        error_message = "The file was not found. Please try uploading the file again."
    except pd.errors.EmptyDataError:
        error_message = "The file is empty. Please upload a valid CSV file."
    except pd.errors.ParserError:
        error_message = "The file could not be parsed. Ensure it is a valid CSV format."
    except Exception as e:
        error_message = str(e)

    # Render an error page with the error message
    return render(request, 'data_analysis/error.html', {'error_message': error_message})
