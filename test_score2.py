from langfuse import observe, get_client
client = get_client()

@observe()
def my_trace():
    client.update_current_trace(name="test_trace")
    client.score_current_trace(name="test_score", value=1.0)

my_trace()
client.flush()
print("Score tracked!")
