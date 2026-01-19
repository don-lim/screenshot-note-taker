import paddle
import sys

print(f"Python Version: {sys.version}")
print(f"Paddle Version: {paddle.__version__}")
print(f"Paddle is compiled with CUDA: {paddle.is_compiled_with_cuda()}")
print(f"GPU Device Count: {paddle.device.cuda.device_count()}")
print(f"Current Device: {paddle.get_device()}")

if paddle.is_compiled_with_cuda():
    try:
        # Simple tensor operation on GPU
        x = paddle.to_tensor([1.0, 2.0, 3.0], place=paddle.CUDAPlace(0))
        print("Successfully created a tensor on GPU.")
    except Exception as e:
        print(f"Error creating tensor on GPU: {e}")
else:
    print("Warning: Paddle is NOT compiled with CUDA support.")
