"""Unit tests for the pipelines.

This module contains tests for the PMSI sampling and profile-generation pipelines.
"""

from pathlib import Path
import tempfile
import pytest

from pipelines.pmsi_sampling.pipeline import PMSISamplingPipeline
from pipelines.profile_generation.pipeline import ProfileGenerationPipeline


class TestPMSISamplingPipeline:
    """Test the PMSI sampling pipeline."""

    def test_initialization(self):
        """Test that the PMSISamplingPipeline can be initialized."""
        config = {"data": {"input": "/tmp", "output": "/tmp"}}
        prompt = {"generate": {"system_prompt": "Test prompt"}}
        servers = {"ollama": {"host": "http://localhost:11434", "model": "mistral"}}

        pipeline = PMSISamplingPipeline(config=config, prompt=prompt, servers=servers)
        assert pipeline.name == "pmsi_sampling"

    def test_check_data_is_not_implemented(self):
        """Test that PMSI data preparation remains explicitly unimplemented."""
        config = {"data": {"input": "/tmp", "output": "/tmp"}}
        prompt = {"generate": {"system_prompt": "Test prompt"}}
        servers = {"ollama": {"host": "http://localhost:11434", "model": "mistral"}}

        pipeline = PMSISamplingPipeline(config=config, prompt=prompt, servers=servers)

        assert pipeline.check_data() is NotImplemented


class TestProfileGenerationPipeline:
    """Test the profile-generation pipeline."""

    def test_initialization(self):
        """Test that the ProfileGenerationPipeline can be initialized."""
        config = {
            "data": {
                "input": "/tmp",
                "output": "/tmp",
                "referentials": "/tmp/referentials"
            }
        }
        prompt = {"generate": {"system_prompt": "Test prompt"}}
        servers = {"ollama": {"host": "http://localhost:11434", "model": "mistral"}}

        pipeline = ProfileGenerationPipeline(config=config, prompt=prompt, servers=servers)
        assert pipeline.name == "profile_generation"

    def test_check_data_creates_output_dir(self):
        """Test that profile-generation check_data prepares the output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "reports" / "profile_generation"
            config = {
                "data": {
                    "input": str(Path(tmpdir) / "data" / "profile_generation"),
                    "output": str(output_dir),
                    "referentials": str(Path(tmpdir) / "data" / "profile_generation" / "referentials"),
                }
            }
            prompt = {"generate": {"system_prompt": "Test prompt"}}
            servers = {"ollama": {"host": "http://localhost:11434", "model": "mistral"}}

            pipeline = ProfileGenerationPipeline(config=config, prompt=prompt, servers=servers)
            pipeline.check_data()

            assert output_dir.exists()


class TestPipelineIntegration:
    """Test the integration of pipelines with the runner."""

    def test_pipelines_are_registered(self):
        """Test that pipelines are correctly registered in the runner."""
        from runner import PIPELINES

        assert "pmsi_sampling" in PIPELINES
        assert "profile_generation" in PIPELINES
        assert PIPELINES["pmsi_sampling"] == PMSISamplingPipeline
        assert PIPELINES["profile_generation"] == ProfileGenerationPipeline
