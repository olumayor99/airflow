"""
### Dynamically map the S3CopyObjectOperator over source/destination pairs

Simple DAG that shows how .map can be used together with .expand_kwargs to dynamically
map over sets of parameters derived from an upstream task.
"""

from airflow.decorators import dag, task
from datetime import datetime, timedelta
from supabase import create_client, Client
import os 
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import json
import time
import subprocess

default_args = {
	'owner': 'jc',
	'retries': 0,
	'retry_delay': timedelta(minutes=2)
}
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
bucket_name: str = "credentials"
supabase_client: Client = create_client(url, key)
nodejs_script_path = './nodejs/opinion.js'

def upload_files(client):

		# Assuming you have the Supabase client already defined as 'client'
		bucket_name = "credentials"  # Replace with your actual bucket name
		local_folder_path = "./clients/"  # Replace with the actual local folder path

		# Iterate over files in the local folder
		for file_name in os.listdir(local_folder_path):
			if file_name.startswith("_opinion_") and file_name.endswith(".pdf"):
				# Extract RFC from the file name
				rfc = file_name[len("_opinion_"):-len(".pdf")]

				# Construct the source path
				source_path = os.path.join(local_folder_path, file_name)

				# Construct the destination path in the storage
				destination_path = f"/{rfc}/{file_name}"


				# Upload the file to Supabase storage
				try:
					with open(source_path, 'rb') as file:
						client.storage.from_(bucket_name).upload(destination_path, file)
					print(f"File {file_name} uploaded successfully.")
				except Exception as e:
					print(f"Error uploading file {file_name}: {e}")

@dag(
	start_date=datetime(2023, 5, 1),
	schedule=None,
	catchup=False,
	dag_id='opt_dag_v1',
	default_args=default_args,
	description='This is our first dag that we write',
	schedule_interval='@daily'
)
def map_and_reduce():
	# dynamically mapped task iterating over list returned by an upstream task
	@task
	def download_credentials(client, rfc, password, bucket_name, **kwargs):
		print(rfc)
		# Use rfc_data as needed in the download_credentials function
		os.makedirs(f"./clients/{rfc}", exist_ok=True)
		# Download and write the key file
		with open(f"./clients/{rfc}/{rfc}.key", 'wb+') as key_file:
			res_key = client.storage.from_(bucket_name).download(f"{rfc}/{rfc}.key")
			key_file.write(res_key)

		# Download and write the cer file
		with open(f"./clients/{rfc}/{rfc}.cer", 'wb+') as cer_file:
			res_cer = client.storage.from_(bucket_name).download(f"{rfc}/{rfc}.cer")
			cer_file.write(res_cer)
		
		time.sleep(1)
		

	@task
	def select_info(client,):
		try:
			# Modify the table name and columns as needed
			data = client.table("info").select("rfc","password").execute().data
			
			if data:
				print(data)
				return data
			else:
				return []
		except Exception as e:
			print(f"Error selecting RFCs: {e}")
	
	@task
	def node_download(rfc,password):
		print(rfc,password)
		# Specify the path to your Node.js script
		nodejs_script_path = './nodejs/opinion.js'

		# Run the Node.js script using subprocess
		try:
			subprocess.run(['node', nodejs_script_path, f"./clients/{rfc}/{rfc}.key", f"./clients/{rfc}/{rfc}.cer", password, rfc], check=True)
		except subprocess.CalledProcessError as e:
			print(f"Error running Node.js script: {e}")

	select_task = select_info(supabase_client,)

	download_task = download_credentials.partial(client=supabase_client,
								bucket_name="credentials",
								).expand_kwargs(select_task)
	node_task = node_download.partial().expand_kwargs(select_task)
	#opinion_task = BashOperator.partial(task_id="Opiniones", cwd = "/home/jc/Documents/SideProjects/airflow").expand_kwargs(create_command(supabase_client,))
	move_files_task = BashOperator(
            task_id=f'move_files',
            bash_command=f'mv ~/Downloads/_opinion_* ./clients/',
			cwd = "."
        )
		
	
	upload_files_task = PythonOperator(
		task_id="upload_files",
		python_callable=upload_files,  # Corrected the function name
		op_args=[supabase_client,],  # Pass any additional arguments here
	)

	delete_files_task = BashOperator(
            task_id=f'delete_files',
            bash_command=f'rm -r ./clients/*',
			cwd = "."
        )
	
	ls_task = BashOperator(
            task_id=f'ls_files',
            bash_command=f'ls /opt/',
			cwd = "."
        )
	
	select_task >> [download_task, node_task] >> ls_task >> move_files_task >> upload_files_task >> delete_files_task
	download_task >> node_task


map_and_reduce()