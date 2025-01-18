import os
import streamlit as st
import google.generativeai as genai
import trimesh
import json

# Set your Gemini API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model with generation configuration
generation_config = {
    "temperature": 2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)

# Initialize the chat session
chat_session = model.start_chat(history=[])

st.title("AI CAD Copilot")

user_input = st.text_input("Describe the CAD model you want to create:")

if st.button("Generate Model"):
    if not user_input:
        st.warning("Please enter a description.")
    else:
        try:
            # Send user input to the chat session to get the model description
            response = chat_session.send_message(user_input)

            # Log the raw response for debugging
            st.subheader("Raw Response:")
            st.write(response.text)  # Display the raw response

            # Check if the response text is empty
            if not response.text:
                st.error("The API returned an empty response. Please check the input or try again later.")
            else:
                try:
                    # Attempt to parse the model description into JSON
                    model_description = response.text
                    model_data = json.loads(model_description)

                    meshes = []
                    for part in model_data:
                        if part["type"] == "box":
                            mesh = trimesh.creation.box(extents=[part["width"], part["height"], part["depth"]])
                        elif part["type"] == "cylinder":
                            mesh = trimesh.creation.cylinder(radius=part["radius"], height=part["height"])
                            if "position" in part:
                                mesh.apply_translation(part["position"])
                        elif part["type"] == "sphere":
                            mesh = trimesh.creation.icosphere(radius=part["radius"])
                        else:
                            st.warning(f"Shape type '{part['type']}' not supported yet.")
                            continue
                        meshes.append(mesh)

                    if meshes:
                        if len(meshes) > 1:
                            final_mesh = trimesh.util.concatenate(meshes)
                        else:
                            final_mesh = meshes[0]

                        stl_data = trimesh.exchange.stl.export_stl(final_mesh)

                        st.download_button(
                            label="Download STL",
                            data=stl_data,
                            file_name="model.stl",
                            mime="application/octet-stream",
                        )

                        scene = trimesh.Scene(final_mesh)
                        png = scene.save_image(resolution=[500, 500], visible=True)
                        st.image(png, use_column_width=True)

                    else:
                        st.warning("No valid shapes were generated.")

                except json.JSONDecodeError as e:
                    st.error(f"Gemini returned invalid JSON: {e}")
                    st.write(model_description)  # Display raw response in case of error

        except Exception as e:
            st.error(f"An error occurred: {e}")
