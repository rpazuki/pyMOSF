import pytest

from pyMOSF.core import processFactory, processLogic, processLogicProperty
from pyMOSF.core.pipelines import (
    AbstractProcess,
    Dict,
    ImageProcessingPipeline,
    IncompatibleArgsException,
    ProcessFork,
    ProcessJoined,
    ProcessLogic,
    ProcessLogicProperty,
    ProcessPassThrough,
)

# filepath: pyMOF/image_processing/test_pipelines.py


def test_dict_missing_key():
    d = Dict()
    assert d['missing_key'] is None
    assert d.missing_key is None


class TestIncompatibleProcess1(AbstractProcess):
    def __call__(self, image, **kwargs) -> Dict:
        return Dict(image=image, result="test1")


class TestIncompatibleProcess2(AbstractProcess):
    def __call__(self, contour, **kwargs) -> Dict:
        return Dict(contour=contour, result="test2")


def test_incompatible_args_exception():
    with pytest.raises(IncompatibleArgsException) as excinfo:
        process1 = TestIncompatibleProcess1()
        process2 = TestIncompatibleProcess2()
        joined = process1 >> process2
        _ = joined(image=None)
    assert (str(excinfo.value) ==
            "The process 'TestIncompatibleProcess2' received incompatible"
            " payload from the previous process 'TestIncompatibleProcess1'.")


class TestProcess(AbstractProcess):
    def __call__(self, **kwargs) -> Dict:
        return Dict(result="test")


class TestAlternativeProcess(AbstractProcess):
    def __call__(self, **kwargs) -> Dict:
        return Dict(result="test")


def test_process_logic():
    @processLogic
    def logic_func(value, **kwargs):
        return Dict(value=value, result="logic")

    process = logic_func()
    assert isinstance(process, ProcessLogic)
    result = process(value="value")
    assert result == Dict(value="value", result="logic")


def test_process_logic_property():
    class AClass:
        @processLogicProperty
        def logic_func(self, value, **kwargs):
            return Dict(value=value, result="logic")

    c = AClass()
    process = c.logic_func
    assert isinstance(process, ProcessLogicProperty)
    result = process(value="value")
    assert result == Dict(value="value", result="logic")


def test_process_factory():
    @processFactory(cache=False)
    def factory_func(flg: bool):
        if flg:
            return TestProcess()
        else:
            return TestAlternativeProcess()

    process = factory_func(flg=True)
    assert isinstance(process, TestProcess)
    process2 = factory_func(flg=False)
    assert isinstance(process2, TestAlternativeProcess)


def test_cached_process_factory():
    @processFactory(cache=True)
    def factory_func(flg: bool):
        if flg:
            return TestProcess()
        else:
            return TestAlternativeProcess()

    process = factory_func(flg=True)
    assert isinstance(process, TestProcess)
    process2 = factory_func(flg=False)
    assert isinstance(process2, TestAlternativeProcess)
    # call again
    process3 = factory_func(flg=True)
    assert isinstance(process3, TestProcess)
    process4 = factory_func(flg=False)
    assert isinstance(process4, TestAlternativeProcess)


def test_process_pass_through():
    process = ProcessPassThrough()
    result = process(test="value")
    assert result == Dict(test="value")


def test_process_joined():
    process1 = TestProcess()
    process2 = TestProcess()
    fork = ProcessFork([process1, process2])
    joined = ProcessJoined(fork)
    result = joined()
    assert result == Dict(result="test")


def test_process_fork():
    process1 = TestProcess()
    process2 = TestProcess()
    fork = ProcessFork([process1, process2])
    result = fork()
    assert result == (Dict(result="test"), Dict(result="test"))


def test_image_processing_pipeline():
    process1 = TestProcess()
    process2 = TestProcess()
    pipeline = ImageProcessingPipeline([process1, process2])
    result = pipeline()
    assert result == Dict(result="test")


def test_process_rshift():
    process1 = TestProcess()
    process2 = TestProcess()
    pipeline = process1 >> process2
    assert isinstance(pipeline, ImageProcessingPipeline)
    result = pipeline()
    assert result == Dict(result="test")


def test_process_mul():
    process1 = TestProcess()
    process2 = TestProcess()
    fork = process1 * process2
    assert isinstance(fork, ProcessFork)
    result = fork()
    assert result == (Dict(result="test"), Dict(result="test"))


def test_process_fork_rshift():
    process1 = TestProcess()
    process2 = TestProcess()
    process3 = TestProcess()
    fork = process1 * process2
    pipline = fork >> process3
    assert isinstance(pipline, ImageProcessingPipeline)
    assert isinstance(pipline.processes[0], ProcessJoined)
    result = pipline()
    assert result == Dict(result="test")


def test_process_join_fork_by_empty_dict():
    process1 = TestProcess()
    process2 = TestProcess()
    fork = process1 * process2
    joined = fork / {}
    assert isinstance(joined, ProcessJoined)
    result = joined()
    assert result == Dict(result="test")


def test_process_fork_truediv():
    process1 = TestProcess()
    process2 = TestProcess()
    fork = process1 * process2
    joined = fork / {0: [("result", "result1")], 1: [("result", "result2")]}
    assert isinstance(joined, ProcessJoined)
    result = joined()
    assert result == Dict(result1="test", result2="test")


def test_image_processing_pipeline_rshift():
    process1 = TestProcess()
    process2 = TestProcess()
    pipeline1 = ImageProcessingPipeline([process1])
    pipeline2 = pipeline1 >> process2
    assert isinstance(pipeline2, ImageProcessingPipeline)
    result = pipeline2()
    assert result == Dict(result="test")


def test_image_processing_pipeline_mul():
    process1 = TestProcess()
    process2 = TestProcess()
    pipeline = ImageProcessingPipeline([process1])
    fork = pipeline * process2
    assert isinstance(fork, ProcessFork)
    result = fork()
    assert result == (Dict(result="test"), Dict(result="test"))
