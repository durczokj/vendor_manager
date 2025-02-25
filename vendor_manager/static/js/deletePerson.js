function deletePerson(event, resourceUrlPattern, resourceId, csrf_token) {
  event.preventDefault();
  const url = resourceUrlPattern.replace('0', resourceId);
  console.log('Deleting URL:', url);

  fetch(url, {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': csrf_token,
      'Content-Type': 'application/json'
    }
  }).then(response => {
    if (response.ok) {
      console.log('Person deleted successfully');
      location.reload();
    } else {
      console.log('Failed to delete the person');
      alert('Failed to delete the person.');
    }
  }).catch(error => {
    console.error('Error:', error);
    alert('Failed to delete the person.');
  });
}
