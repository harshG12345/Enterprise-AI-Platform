"""Unit tests for SQLAlchemy models and relationships."""

import uuid

import pytest
from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.models import (
    AuditLog,
    Dataset,
    DatasetStatus,
    Experiment,
    JobStatus,
    ModelStatus,
    Prediction,
    Project,
    TaskType,
    TrainedModel,
    TrainingJob,
    User,
    UserRole,
)


@pytest.mark.asyncio
async def test_create_user_and_project():
    """Verify user creation and cascaded project relationship."""
    async with AsyncSessionLocal() as session:
        user = User(
            id=uuid.uuid4(),
            email=f"user_{uuid.uuid4().hex[:8]}@example.com",
            full_name="ML Engineer",
            password_hash="argon2_hashed_value",
            role=UserRole.DATA_SCIENTIST,
        )
        session.add(user)
        await session.commit()

        # Create project under user
        project = Project(
            id=uuid.uuid4(),
            name="Churn Prediction System",
            description="Predict customer churn probability",
            owner_id=user.id,
        )
        session.add(project)
        await session.commit()

        # Query back and assert
        stmt = select(Project).where(Project.id == project.id)
        result = await session.execute(stmt)
        retrieved_project = result.scalar_one()

        assert retrieved_project.name == "Churn Prediction System"
        assert retrieved_project.owner_id == user.id
        assert retrieved_project.created_at is not None


@pytest.mark.asyncio
async def test_full_ml_entity_pipeline_models():
    """Verify dataset, experiment, training job, trained model, prediction and audit log entities."""
    async with AsyncSessionLocal() as session:
        user = User(
            id=uuid.uuid4(),
            email=f"ds_{uuid.uuid4().hex[:8]}@example.com",
            full_name="Lead Data Scientist",
            password_hash="argon2_hash",
            role=UserRole.ADMIN,
        )
        session.add(user)
        await session.commit()

        project = Project(
            id=uuid.uuid4(),
            name="Fraud Detection",
            owner_id=user.id,
        )
        session.add(project)
        await session.commit()

        dataset = Dataset(
            id=uuid.uuid4(),
            project_id=project.id,
            filename="transactions.csv",
            storage_path="data/uploads/transactions.csv",
            file_size=1048576,
            row_count=50000,
            column_count=12,
            schema_metadata={"target": "is_fraud", "features": ["amount", "age", "location"]},
            status=DatasetStatus.VALIDATED,
        )
        session.add(dataset)
        await session.commit()

        experiment = Experiment(
            id=uuid.uuid4(),
            project_id=project.id,
            dataset_id=dataset.id,
            name="Fraud_RandomForest_Exp",
            mlflow_experiment_id="exp_123",
        )
        session.add(experiment)
        await session.commit()

        training_job = TrainingJob(
            id=uuid.uuid4(),
            project_id=project.id,
            dataset_id=dataset.id,
            user_id=user.id,
            status=JobStatus.SUCCESS,
            target_column="is_fraud",
            task_type=TaskType.CLASSIFICATION,
            celery_task_id="celery-task-999",
        )
        session.add(training_job)
        await session.commit()

        model = TrainedModel(
            id=uuid.uuid4(),
            project_id=project.id,
            dataset_id=dataset.id,
            experiment_id=experiment.id,
            name="Fraud_RF_Classifier",
            version="v1.0.0",
            task_type="classification",
            framework="scikit-learn",
            metrics={"accuracy": 0.985, "f1": 0.942, "roc_auc": 0.991},
            artifact_path="data/models/fraud_rf_v1.joblib",
            mlflow_run_id="run-456",
            status=ModelStatus.PRODUCTION,
        )
        session.add(model)
        await session.commit()

        prediction = Prediction(
            id=uuid.uuid4(),
            model_id=model.id,
            user_id=user.id,
            input_data={"amount": 450.0, "age": 34, "location": "NY"},
            prediction={"is_fraud": 0, "probability": 0.03},
            latency_ms=14.2,
        )
        session.add(prediction)

        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user.id,
            action="MODEL_PROMOTION",
            resource_type="TRAINED_MODEL",
            resource_id=str(model.id),
            ip_address="127.0.0.1",
            metadata_json={"previous_status": "STAGING", "new_status": "PRODUCTION"},
        )
        session.add(audit)
        await session.commit()

        # Query all and assert
        pred_res = await session.execute(select(Prediction).where(Prediction.id == prediction.id))
        retrieved_pred = pred_res.scalar_one()
        assert retrieved_pred.latency_ms == 14.2
        assert retrieved_pred.prediction["is_fraud"] == 0

        audit_res = await session.execute(select(AuditLog).where(AuditLog.id == audit.id))
        retrieved_audit = audit_res.scalar_one()
        assert retrieved_audit.action == "MODEL_PROMOTION"
        assert retrieved_audit.resource_type == "TRAINED_MODEL"
