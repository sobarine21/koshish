import streamlit as st
import google.generativeai as palm
import trimesh
import json

# Set your Gemini API key
palm.configure(api_key="YOUR_GEMINI_API_KEY")

# Choose your model
model = palm.GenerativeModel("models/gemini-pro")

st.title("AI CAD Copilot")

user_input = st.text_input("Describe the CAD model you want to create:")

if st.button("Generate Model"):
    if not user_input:
        st.warning("Please enter a description.")
    else:
        try:
            prompt = f"""
            You are an expert CAD modeler. Based on the user's description, generate a concise description of the geometric primitives and their parameters needed to create the 3D model. Focus on simple shapes like boxes, cylinders, spheres, cones, etc. Provide the output in a structured JSON format suitable for parsing, for example:

            ```json
            [
              {{"type": "box", "width": 10, "height": 5, "depth": 3}},
              {{"type": "cylinder", "radius": 2, "height": 8, "position": [5, 0, 0]}}
            ]
            ```

            User Description: {user_input}
            """

            # Correct way to generate text with Gemini
            response = model.generate_text(prompt=prompt)

            model_description = response.result

            try:
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
                st.write(model_description)

        except Exception as e:
            st.error(f"An error occurred: {e}")
