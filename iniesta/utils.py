
def filter_list_to_filter_policies(event_key, filter_list):
    processed_filters = []

    for filters in filter_list:
        event = filters.split('.')
        assert len(event) == 2

        if event[1] == "*":
            processed_filters.append({"prefix": f"{event[0]}."})
        else:
            processed_filters.append(filters)

    if len(processed_filters) > 0:
        filter_policies = {event_key: processed_filters}
    else:
        filter_policies = {}

    return filter_policies
