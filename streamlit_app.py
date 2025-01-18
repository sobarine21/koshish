import streamlit as st
import google.generativeai as palm
import trimesh
import numpy as np
import io
import base64

# Set your Palm API key
palm.configure(api_key="YOUR_PALM_API_KEY")

# Streamlit app
st.title("AI CAD Copilot")

user_input = st.text_input("Describe the CAD model you want to create:")

if st.button("Generate Model"):
    if not user_input:
        st.warning("Please enter a description.")
    else:
        try:
            # Gemini Prompt Engineering
            prompt = f"""
            You are an expert CAD modeler. Based on the user's description, generate a concise description of the geometric primitives and their parameters needed to create the 3D model. Focus on simple shapes like boxes, cylinders, spheres, cones, etc. Provide the output in a structured format suitable for parsing, for example:

            ```
            [
              {{"type": "box", "width": 10, "height": 5, "depth": 3}},
              {{"type": "cylinder", "radius": 2, "height": 8, "position": [5, 0, 0]}}
            ]
            ```

            User Description: {user_input}
            """

            # Use Gemini to get structured model description
            response = palm.generate_text(
                model="models/text-bison-001",  # Or a more suitable model
                prompt=prompt,
                temperature=0.0,  # Adjust for creativity vs. accuracy
                max_output_tokens=512,
            )

            model_description = response.result

            # Attempt to parse the JSON output from Gemini
            try:
                import json
                model_data = json.loads(model_description)

                # Generate mesh using trimesh
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
                    # Add more shapes as needed (cone, torus, etc.)
                    else:
                        st.warning(f"Shape type '{part['type']}' not supported yet.")
                        continue
                    meshes.append(mesh)

                if meshes:
                    # Combine meshes if multiple parts
                    if len(meshes) > 1:
                        final_mesh = trimesh.util.concatenate(meshes)
                    else:
                        final_mesh = meshes[0]

                    # Export to STL (or other format) and display
                    stl_data = trimesh.exchange.stl.export_stl(final_mesh)

                    st.download_button(
                        label="Download STL",
                        data=stl_data,
                        file_name="model.stl",
                        mime="application/octet-stream",
                    )

                    # Display the mesh in the streamlit app
                    scene = trimesh.Scene(final_mesh)
                    png = scene.save_image(resolution=[500, 500], visible=True)
                    st.image(png, use_column_width=True)


                else:
                    st.warning("No valid shapes were generated.")

            except json.JSONDecodeError:
                st.error("Gemini returned invalid JSON. Please refine your prompt or try again.")
                st.write(model_description) # Display the raw Gemini output for debugging.

        except Exception as e:
            st.error(f"An error occurred: {e}")
