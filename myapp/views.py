# views.py
from django.shortcuts import render
import requests
from .forms import ImageUploadForm
from inference_sdk import InferenceHTTPClient
FOOD_NUTRIENT_MAPPING = {
    'Indian Bread': {'calories': 114, 'protein': 3.4, 'fat': 3.7, 'carbohydrates': 18.5},
    'Rasgulla': {'calories': 106, 'protein': 10, 'fat': 30, 'carbohydrates': 59},
    'Poha':{'calories': 180, 'protein': 9, 'fat': 71, 'carbohydrates': 100},
    'Paneer':{'calories': 180, 'protein': 9, 'fat': 71, 'carbohydrates': 100}
}

CLASS_LABELS_MAPPING = {
    '0': 'Indian Bread',
    '1': 'Rasgulla',
    '2': 'Biryani',
    '3': 'Uttapam',
    '4': 'Paneer',
    '5': 'Poha',
    '6': 'Khichdi',
    '7': 'Omelette',
    '8': 'Plain Rice',
    '9': 'Dal Makhani',
    '10': 'Rajma',
    '11': 'Poori',
    '12': 'Chole',
    '13': 'Dal',
    '14': 'Sambhar',
    '15': 'Papad',
    '16': 'Gulab Jamun',
    '17': 'Idli',
    '18': 'Vada',
    '19': 'Dosa'
}

def scan_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the uploaded file to a temporary location
            uploaded_file = request.FILES['image']
            file_path = handle_uploaded_file(uploaded_file)

            # Call the InferenceHTTPClient with the file path
            CLIENT = InferenceHTTPClient(
                api_url="http://detect.roboflow.com",
                api_key="sAdRD9RvWmx3ozjS6U5r"
            )
            result = CLIENT.infer(file_path, model_id="nutriscan-final/2")            
            print("Result dictionary:", result)

            # Check the structure of the result dictionary
            if 'predictions' in result and result['predictions']:
                #bounding_box = {'x': 107.5, 'y': 77.5, 'width': 91.0, 'height': 65.0}
               
            # Convert pixel coordinates to physical dimensions (centimeters)
                pixel_to_cm_conversion = 0.1  # Conversion factor: 1 pixel = 0.1 cm
                
                a=result.get('predictions')
                bounding_box_width_cm =a[0].get('width') * pixel_to_cm_conversion
                bounding_box_height_cm = a[0].get('height') * pixel_to_cm_conversion
                
                bounding_box_area_cm2 = bounding_box_width_cm * bounding_box_height_cm
                conversion_factor_g_per_cm2 = 0.25 
                weight_estimate_grams = bounding_box_area_cm2 * conversion_factor_g_per_cm2
                print("width:",bounding_box_width_cm)
                print("Estimated weight:", weight_estimate_grams, "grams")
                detected_food_names = [CLASS_LABELS_MAPPING.get(pred.get('class'), "Unknown") for pred in result['predictions']]
                # Join the detected food names into a single string
                detected_food_name = ", ".join(detected_food_names)
                query = '{}g {}'.format(weight_estimate_grams, detected_food_name)
                nutrient_estimations = estimate_nutrients(query)
                # Render the result along with the detected food names and nutrient estimations
                return render(request, 'result.html', {'detected_food_name': detected_food_name, 'nutrient_estimations': nutrient_estimations})
            else:
                # Handle the case when no predictions are returned
                return render(request, 'error.html', {'message': 'No predictions found.'})
    else:
        form = ImageUploadForm()
    return render(request, 'scan_image.html', {'form': form})


def estimate_nutrients(query):
    # Construct the API URL with the query parameter
    api_url = 'https://api.api-ninjas.com/v1/nutrition?query={}'.format(query)
    
    # Make a GET request to the API
    response = requests.get(api_url, headers={'X-Api-Key': 'YDlWU946cxff0l0aCAOqbw==vkBstQ9Un6zb2tbR'})
    
    # Check if the request was successful (status code 200)
    if response.status_code == requests.codes.ok:
        # Parse the JSON response
        nutrient_data = response.json()
        
        # Extract nutrient information from the response
        nutrients = {
            'calories': nutrient_data[0].get('calories', 0),
            'protein': nutrient_data[0].get('protein_g', 0),
            'fat': nutrient_data[0].get('fat_total_g', 0),
            'carbohydrates': nutrient_data[0].get('carbohydrates_total_g', 0),
        }
        
        return nutrients
    else:
        print("Error:", response.status_code, response.text)
        return {}


def handle_uploaded_file(uploaded_file):
    file_path = 'temp_image.jpg'
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return file_path


