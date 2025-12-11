import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException

def submit_job(job_name: str):
    """Submit a job to Kubernetes cluster."""
    try:
        # Load Kubernetes config
        # This will use ~/.kube/config or in-cluster config if running in a pod
        try:
            config.load_incluster_config()
            print("[AutoDev] Using in-cluster Kubernetes config")
        except:
            config.load_kube_config()
            print("[AutoDev] Using local kubeconfig")

        # Get namespace from env or use default
        namespace = os.getenv("K8S_NAMESPACE", "default")

        # Create Kubernetes API client
        batch_v1 = client.BatchV1Api()

        # Define the job
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=job_name),
            spec=client.V1JobSpec(
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": job_name}),
                    spec=client.V1PodSpec(
                        restart_policy="Never",
                        containers=[
                            client.V1Container(
                                name=job_name,
                                image=os.getenv("K8S_JOB_IMAGE", "busybox:latest"),
                                command=["echo", f"Running job: {job_name}"]
                            )
                        ]
                    )
                )
            )
        )

        # Submit the job
        response = batch_v1.create_namespaced_job(
            namespace=namespace,
            body=job
        )

        print(f"[AutoDev] Job '{job_name}' created successfully in namespace '{namespace}'")
        print(f"[AutoDev] Job UID: {response.metadata.uid}")
        print(f"[AutoDev] Status: {response.status}")

        return {
            "job_name": job_name,
            "namespace": namespace,
            "uid": response.metadata.uid,
            "status": "created"
        }

    except ApiException as e:
        print(f"[AutoDev] Kubernetes API error: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }
    except Exception as e:
        print(f"[AutoDev] Error submitting job: {e}")
        print("[AutoDev] Make sure kubectl is configured and you have access to a K8s cluster")
        return {
            "error": str(e),
            "status": "failed"
        }
