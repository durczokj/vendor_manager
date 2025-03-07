function deleteResource(event, resourceUrlPattern, resourceId, csrf_token, redirectUrl = null) {
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
      console.log('Resource deleted successfully');
      if (redirectUrl) {
        window.location.href = redirectUrl;
      } else {
        location.reload();
      }
    } else {
      console.log('Failed to delete the resource');
      alert('Failed to delete the resource.');
    }
  }).catch(error => {
    console.error('Error:', error);
    alert('Failed to delete the resource.');
  });
}
