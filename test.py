import requests
import io
import base64
from PIL import Image
import matplotlib.pyplot as plt
import json

def generate_and_show_image(prompt):
    # API endpoint
    url = "https://pranavai.onrender.com/generate"
    
    # Prepare the request data
    data = {
        "prompt": prompt
    }
    
    # Make the API request
    print(f"Generating image for prompt: '{prompt}'...")
    response = requests.post(url, json=data)
    
    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        
        print(f"Success! Seed used: {result.get('seed', 'unknown')}")
        
        # Check if images array is in the response
        if 'images' in result and len(result['images']) > 0:
            # Get the first image from the images array
            image_data = result['images'][0]
            
            # Extract the base64 data from the URL field
            if 'url' in image_data and image_data['url'].startswith('data:image'):
                # Split the data URI to get the base64 part
                base64_data = image_data['url'].split(',')[1]
                
                # Decode the base64 data
                image_bytes = base64.b64decode(base64_data)
                
                # Create an image from the bytes
                image = Image.open(io.BytesIO(image_bytes))
                
                # Display the image
                plt.figure(figsize=(10, 8))
                plt.imshow(image)
                plt.axis('off')
                plt.title(f"Generated image for: {prompt}")
                plt.show()
                
                # Save the image to a file
                output_file = "generated_image.jpg"
                image.save(output_file)
                print(f"Image saved to {output_file}")
                
                return image
            else:
                print("Image URL not found or not in expected format")
        else:
            print("Response does not contain images array")
            print("Available fields in response:", list(result.keys()))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    return None

# Example usage
if __name__ == "__main__":
    prompt = "a beautiful sunset over mountains, cinematic lighting, 4k, detailed"
    image = generate_and_show_image(prompt)